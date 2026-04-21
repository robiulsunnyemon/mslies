from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from datetime import datetime, timedelta
from app.database import db
from app.schemas import (
    UserCreate, UserResponse, UserMeResponse, Token, OtpVerifyRequest, 
    ForgotPasswordRequest, ResetPasswordRequest, UpdateProfileRequest,Login
)
from app.services.auth_service import (
    hash_password, verify_password, create_access_token, 
    create_refresh_token, generate_otp
)
from app.services.email_service import send_otp_email, send_reset_password_email
from app.auth import get_current_user
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    user_with_details = await db.user.find_unique(
        where={"id": current_user.id},
        include={
            "files": {
                "include": {
                    "mcqSets": {
                        "include": {
                            "questions": True
                        }
                    }
                }
            }
        }
    )
    return user_with_details

@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate, background_tasks: BackgroundTasks):
    # Check if user already exists
    existing_user = await db.user.find_unique(where={"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user (unverified)
    hashed_password = hash_password(user_data.password)
    user = await db.user.create(
        data={
            "email": user_data.email,
            "fullname": user_data.fullname,
            "passwordHash": hashed_password,
            "isVerified": False
        }
    )
    
    # Generate and send OTP
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    await db.otp.create(
        data={
            "email": user_data.email,
            "code": otp_code,
            "type": "SIGNUP",
            "expiresAt": expires_at
        }
    )
    
    background_tasks.add_task(send_otp_email, user_data.email, otp_code)
    
    return user

@router.post("/verify-otp")
async def verify_otp(request: OtpVerifyRequest):
    # Check OTP
    otp_record = await db.otp.find_first(
        where={
            "email": request.email,
            "code": request.code,
            "expiresAt": {"gt": datetime.utcnow()}
        },
        order={"createdAt": "desc"}
    )
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # Mark user as verified
    await db.user.update(
        where={"email": request.email},
        data={"isVerified": True}
    )
    
    # Clean up OTPs
    await db.otp.delete_many(where={"email": request.email})
    
    # Create tokens
    access_token = create_access_token(data={"sub": request.email})
    refresh_token = create_refresh_token(data={"sub": request.email})
    
    # Save refresh token
    user = await db.user.find_unique(where={"email": request.email})
    await db.refreshtoken.create(
        data={
            "token": refresh_token,
            "userId": user.id,
            "expiresAt": datetime.utcnow() + timedelta(days=7)
        }
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login")
async def login(user_data: Login): # Reuse UserCreate for convenience or create LoginRequest
    user = await db.user.find_unique(where={"email": user_data.email})
    if not user or not verify_password(user_data.password, user.passwordHash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.isVerified:
        raise HTTPException(status_code=403, detail="Email not verified")
    
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    # Save refresh token
    await db.refreshtoken.create(
        data={
            "token": refresh_token,
            "userId": user.id,
            "expiresAt": datetime.utcnow() + timedelta(days=7)
        }
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/resend-otp")
async def resend_otp(email: str, background_tasks: BackgroundTasks):
    user = await db.user.find_unique(where={"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    await db.otp.create(
        data={
            "email": email,
            "code": otp_code,
            "type": "SIGNUP",
            "expiresAt": expires_at
        }
    )
    
    background_tasks.add_task(send_otp_email, email, otp_code)
    return {"message": "OTP resent successfully"}

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    user = await db.user.find_unique(where={"email": request.email})
    if not user:
        # For security, don't reveal if user exists. Just return 200.
        return {"message": "If the email exists, an OTP has been sent."}
    
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    await db.otp.create(
        data={
            "email": request.email,
            "code": otp_code,
            "type": "FORGOT_PASSWORD",
            "expiresAt": expires_at
        }
    )
    
    background_tasks.add_task(send_reset_password_email, request.email, otp_code)
    return {"message": "If the email exists, an OTP has been sent."}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    # Verify OTP
    otp_record = await db.otp.find_first(
        where={
            "email": request.email,
            "code": request.code,
            "type": "FORGOT_PASSWORD",
            "expiresAt": {"gt": datetime.utcnow()}
        },
        order={"createdAt": "desc"}
    )
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # Reset Password
    hashed_password = hash_password(request.new_password)
    await db.user.update(
        where={"email": request.email},
        data={"passwordHash": hashed_password}
    )
    
    # Clean up OTPs
    await db.otp.delete_many(where={"email": request.email})
    
    return {"message": "Password reset successfully"}

@router.post("/logout")
async def logout(refresh_token: str):
    await db.refreshtoken.delete(where={"token": refresh_token})
    return {"message": "Logged out successfully"}

@router.post("/refresh")
async def refresh(refresh_token: str):
    token_record = await db.refreshtoken.find_unique(
        where={"token": refresh_token},
        include={"user": True}
    )
    
    if not token_record or token_record.expiresAt < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
    access_token = create_access_token(data={"sub": token_record.user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.put("/update-profile", response_model=UserResponse)
async def update_profile(request: UpdateProfileRequest, current_user: UserResponse = Depends(get_current_user)):
    user = await db.user.update(
        where={"id": current_user.id},
        data={"fullname": request.fullname}
    )
    return user
