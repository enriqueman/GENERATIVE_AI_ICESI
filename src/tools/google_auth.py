"""
Google OAuth Authentication with OTP Verification
"""
import os
import smtplib
import secrets
import hashlib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict
import sqlite3
from models.db import connect_db


class GoogleAuthService:
    """Service for Google OAuth authentication with OTP verification"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from = os.getenv("SMTP_FROM", "")
    
    def generate_otp(self, length: int = 6) -> str:
        """Generate a random OTP code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])
    
    def store_otp(self, email: str, otp_code: str, expires_in_minutes: int = 10) -> bool:
        """Store OTP code in database"""
        conn = connect_db()
        cursor = conn.cursor()
        
        try:
            expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)
            
            cursor.execute("""
                INSERT INTO otp_codes (email, otp_code, expires_at)
                VALUES (?, ?, ?)
            """, (email, otp_code, expires_at.isoformat()))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error storing OTP: {e}")
            return False
        finally:
            conn.close()
    
    def send_otp_email(self, email: str, otp_code: str) -> bool:
        """Send OTP code via email"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Código de verificación - Universidad ICESI"
            msg['From'] = self.smtp_from
            msg['To'] = email
            
            # Create HTML email
            html_body = f"""
            <html>
              <body style="font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 40px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                  <!-- Header -->
                  <div style="text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 3px solid #003366;">
                    <h1 style="color: #003366; font-size: 24px; margin: 0; font-weight: bold;">Universidad ICESI</h1>
                    <p style="color: #666; font-size: 14px; margin: 5px 0 0 0;">Sistema de Recomendación de Posgrados</p>
                  </div>
                  
                  <!-- Content -->
                  <h2 style="color: #003366; text-align: center; font-size: 20px; margin-bottom: 20px;">🔐 Verificación de Correo Electrónico</h2>
                  <p style="font-size: 16px; color: #333; line-height: 1.6;">Estimado/a candidato/a,</p>
                  <p style="font-size: 16px; color: #333; line-height: 1.6;">Para continuar con el proceso de recomendación de posgrados, necesitamos verificar tu correo electrónico. Tu código de verificación es:</p>
                  
                  <!-- OTP Code -->
                  <div style="text-align: center; margin: 35px 0;">
                    <span style="font-size: 36px; font-weight: bold; color: #003366; letter-spacing: 8px; padding: 20px 40px; background-color: #f0f4f8; border: 2px solid #003366; border-radius: 6px; display: inline-block; font-family: 'Courier New', monospace;">
                      {otp_code}
                    </span>
                  </div>
                  
                  <!-- Instructions -->
                  <div style="background-color: #f0f4f8; padding: 15px; border-radius: 6px; margin: 25px 0;">
                    <p style="font-size: 14px; color: #555; margin: 0; line-height: 1.6;">
                      <strong>⏱️ Este código expira en 10 minutos.</strong><br>
                      Por favor, ingresa este código en el sistema para continuar con tu proceso de recomendación.
                    </p>
                  </div>
                  
                  <p style="font-size: 14px; color: #666; line-height: 1.6;">Si no solicitaste este código, puedes ignorar este mensaje de forma segura.</p>
                  
                  <!-- Footer -->
                  <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
                  <div style="text-align: center;">
                    <p style="font-size: 12px; color: #999; margin: 5px 0;">
                      <strong>Universidad ICESI</strong><br>
                      Sistema de Recomendación de Posgrados
                    </p>
                    <p style="font-size: 11px; color: #bbb; margin: 10px 0 0 0;">
                      📧 admisiones.posgrados@icesi.edu.co<br>
                      🌐 www.icesi.edu.co/posgrados
                    </p>
                  </div>
                </div>
              </body>
            </html>
            """
            
            text_body = f"""
            Universidad ICESI - Sistema de Recomendación de Posgrados
            ===========================================================
            
            Verificación de Correo Electrónico
            
            Estimado/a candidato/a,
            
            Para continuar con el proceso de recomendación de posgrados, necesitamos verificar tu correo electrónico.
            
            Tu código de verificación es: {otp_code}
            
            Este código expira en 10 minutos.
            
            Por favor, ingresa este código en el sistema para continuar con tu proceso de recomendación.
            
            Si no solicitaste este código, puedes ignorar este mensaje de forma segura.
            
            --
            Universidad ICESI
            Sistema de Recomendación de Posgrados
            
            📧 admisiones.posgrados@icesi.edu.co
            🌐 www.icesi.edu.co/posgrados
            """
            
            # Add both HTML and text versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            if not self.smtp_user or not self.smtp_password:
                print("SMTP credentials not configured. Skipping email send.")
                return False
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"OTP email sent to {email}")
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def verify_otp(self, email: str, otp_code: str) -> bool:
        """Verify OTP code"""
        conn = connect_db()
        cursor = conn.cursor()
        
        try:
            # Check if OTP exists and is valid
            cursor.execute("""
                SELECT id FROM otp_codes
                WHERE email = ? AND otp_code = ? AND used = 0
                AND expires_at > datetime('now')
                ORDER BY created_at DESC
                LIMIT 1
            """, (email, otp_code))
            
            result = cursor.fetchone()
            
            if result:
                # Mark OTP as used
                cursor.execute("""
                    UPDATE otp_codes SET used = 1 WHERE id = ?
                """, (result[0],))
                conn.commit()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error verifying OTP: {e}")
            return False
        finally:
            conn.close()
    
    def create_or_update_google_user(self, email: str, google_id: str, name: str, 
                                     picture_url: str = None) -> Optional[Dict]:
        """Create or update Google authenticated user"""
        conn = connect_db()
        cursor = conn.cursor()
        
        try:
            # Check if user exists
            cursor.execute("""
                SELECT id, email_verified FROM google_auth WHERE email = ?
            """, (email,))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing user
                cursor.execute("""
                    UPDATE google_auth 
                    SET google_id = ?, name = ?, picture_url = ?, last_login = ?
                    WHERE email = ?
                """, (google_id, name, picture_url, datetime.now().isoformat(), email))
                user_id = existing[0]
                email_verified = existing[1]
            else:
                # Create new user
                cursor.execute("""
                    INSERT INTO google_auth (email, google_id, name, picture_url, last_login)
                    VALUES (?, ?, ?, ?, ?)
                """, (email, google_id, name, picture_url, datetime.now().isoformat()))
                user_id = cursor.lastrowid
                email_verified = 0
            
            conn.commit()
            
            return {
                "id": user_id,
                "email": email,
                "google_id": google_id,
                "name": name,
                "picture_url": picture_url,
                "email_verified": email_verified
            }
            
        except Exception as e:
            print(f"Error creating/updating Google user: {e}")
            return None
        finally:
            conn.close()
    
    def mark_email_verified(self, email: str) -> bool:
        """Mark email as verified"""
        conn = connect_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE google_auth 
                SET email_verified = 1 
                WHERE email = ?
            """, (email,))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Error marking email as verified: {e}")
            return False
        finally:
            conn.close()
    
    def get_google_user_by_email(self, email: str) -> Optional[Dict]:
        """Get Google user by email"""
        conn = connect_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, email, google_id, name, picture_url, email_verified, created_at, last_login
                FROM google_auth WHERE email = ?
            """, (email,))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    "id": result[0],
                    "email": result[1],
                    "google_id": result[2],
                    "name": result[3],
                    "picture_url": result[4],
                    "email_verified": result[5],
                    "created_at": result[6],
                    "last_login": result[7]
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting Google user: {e}")
            return None
        finally:
            conn.close()
    
    def generate_auth_url(self, redirect_uri: str) -> str:
        """Generate Google OAuth authentication URL"""
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        
        if not google_client_id:
            raise ValueError("GOOGLE_CLIENT_ID not configured")
        
        # Google OAuth scopes
        scopes = "openid email profile"
        
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={google_client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scopes}&"
            f"response_type=code&"
            f"access_type=offline&"
            f"prompt=consent&"
            f"state={state}"
        )
        
        return auth_url, state
    
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Optional[Dict]:
        """Exchange authorization code for tokens"""
        import httpx
        
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        
        if not google_client_id or not google_client_secret:
            raise ValueError("Google OAuth credentials not configured")
        
        try:
            token_url = "https://oauth2.googleapis.com/token"
            
            response = httpx.post(
                token_url,
                data={
                    "code": code,
                    "client_id": google_client_id,
                    "client_secret": google_client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            
            print(f"Error exchanging code: {response.text}")
            return None
            
        except Exception as e:
            print(f"Error exchanging code for token: {e}")
            return None
    
    def get_user_info_from_token(self, access_token: str) -> Optional[Dict]:
        """Get user information from Google access token"""
        import httpx
        
        try:
            response = httpx.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            
            print(f"Error getting user info: {response.text}")
            return None
            
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None


# Singleton instance
google_auth_service = GoogleAuthService()

