from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from backend.core.db import users_col
from backend.core.config import settings
from backend.auth.oidc import oauth
from backend.auth.utils import create_access_token
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/login/google")
async def google_login(request: Request):
    redirect_uri = settings.GOOGLE_REDIRECT_URI

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        access_type="offline",
        prompt="consent"
    )


@router.get("/google/callback")
async def google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        
        raise HTTPException(status_code=400, detail=f"OAuth Error: {str(e)}")
    user_info = token.get('userinfo')
    
    user = await users_col.find_one({"email": user_info['email']})
    
    user_data = {
        "email": user_info['email'],
        "name": user_info.get('name'),
        "google_token": token,
        "last_login": datetime.utcnow()
    }
    
    if not user:
        result = await users_col.insert_one(user_data)
        user_id = str(result.inserted_id)
    else:
        user_id = str(user["_id"])
        await users_col.update_one({"_id": user["_id"]}, {"$set": user_data})

    access_token = create_access_token(data={"sub": user_id, "email": user_info['email']})
    return RedirectResponse(url=f"/static/dashboard.html?token={access_token}")