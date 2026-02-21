"""
Email Service for sending recommendation emails
"""
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict
import environ
import pathlib

# Configurar environment
env = environ.Env()
env_path = pathlib.Path(__file__).resolve().parent.parent.parent / '.env'
environ.Env.read_env(str(env_path))


class EmailService:
    """Service for sending recommendation emails"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from = os.getenv("SMTP_FROM", "")
    
    def send_recommendation_email(
        self,
        email: str,
        name: str,
        recommendation: str,
        programs: list = None
    ) -> bool:
        """
        Send recommendation email to user
        
        Args:
            email: User email
            name: User name
            recommendation: Recommendation text
            programs: List of recommended programs (optional)
        
        Returns:
            bool: True if sent successfully
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Tu Recomendación de Posgrados - Universidad ICESI"
            msg['From'] = self.smtp_from or self.smtp_user
            msg['To'] = email
            
            # HTML body
            html_body = f"""
            <!DOCTYPE html>
            <html>
              <head>
                <meta charset="utf-8">
                <style>
                  body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                  }}
                  .container {{
                    background-color: #ffffff;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                  }}
                  .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    margin-bottom: 30px;
                  }}
                  .header h1 {{
                    margin: 0;
                    font-size: 24px;
                  }}
                  .content {{
                    margin: 20px 0;
                  }}
                  .recommendation {{
                    background-color: #f8f9fa;
                    border-left: 4px solid #667eea;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 4px;
                  }}
                  .programs {{
                    margin: 20px 0;
                  }}
                  .program-item {{
                    background-color: #f0f4f8;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 6px;
                    border-left: 3px solid #667eea;
                  }}
                  .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e0e0e0;
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                  }}
                  .cta-button {{
                    display: inline-block;
                    background-color: #667eea;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                    font-weight: bold;
                  }}
                </style>
              </head>
              <body>
                <div class="container">
                  <div class="header">
                    <h1>🎓 Universidad ICESI</h1>
                    <p style="margin: 10px 0 0 0;">Sistema de Recomendación de Posgrados</p>
                  </div>
                  
                  <div class="content">
                    <p>Hola <strong>{name}</strong>,</p>
                    
                    <p>Gracias por usar nuestro Sistema de Recomendación de Posgrados. Como solicitaste, te enviamos tu recomendación personalizada.</p>
                    
                    <div class="recommendation">
                      {recommendation.replace(chr(10), '<br>')}
                    </div>
                    
                    {self._format_programs_html(programs) if programs else ''}
                    
                    <div style="text-align: center; margin: 30px 0;">
                      <a href="mailto:admisiones.posgrados@icesi.edu.co" class="cta-button">
                        📧 Contactar Admisiones
                      </a>
                    </div>
                    
                    <p>Nuestro equipo de admisiones está listo para ayudarte en tu proceso de selección de posgrado.</p>
                  </div>
                  
                  <div class="footer">
                    <p><strong>Universidad ICESI</strong></p>
                    <p>📧 admisiones.posgrados@icesi.edu.co</p>
                    <p>📱 WhatsApp: +57 318 765 4321</p>
                    <p>🌐 www.icesi.edu.co/posgrados</p>
                    <p style="margin-top: 15px; color: #999;">
                      Este correo fue generado automáticamente por el Sistema de Recomendación de Posgrados de la Universidad ICESI.
                    </p>
                  </div>
                </div>
              </body>
            </html>
            """
            
            # Plain text body
            text_body = f"""
            Universidad ICESI - Sistema de Recomendación de Posgrados
            ===========================================================
            
            Hola {name},
            
            Gracias por usar nuestro Sistema de Recomendación de Posgrados. Como solicitaste, te enviamos tu recomendación personalizada.
            
            {recommendation}
            
            {self._format_programs_text(programs) if programs else ''}
            
            CONTACTO:
            📧 admisiones.posgrados@icesi.edu.co
            📱 WhatsApp: +57 318 765 4321
            🌐 www.icesi.edu.co/posgrados
            
            Nuestro equipo de admisiones está listo para ayudarte en tu proceso de selección de posgrado.
            
            --
            Universidad ICESI
            Sistema de Recomendación de Posgrados
            """
            
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
            
            print(f"Recommendation email sent to {email}")
            return True
            
        except Exception as e:
            print(f"Error sending recommendation email: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _format_programs_html(self, programs: list) -> str:
        """Format programs list as HTML"""
        if not programs:
            return ""
        
        html = '<div class="programs"><h3>Programas Recomendados:</h3>'
        for i, program in enumerate(programs[:3], 1):
            program_name = program.get("program_name", "Programa")
            score = program.get("score", 0)
            html += f'''
            <div class="program-item">
              <strong>{i}. {program_name}</strong>
              <p style="margin: 5px 0; color: #667eea;">Afinidad: {score}/100</p>
            </div>
            '''
        html += '</div>'
        return html
    
    def _format_programs_text(self, programs: list) -> str:
        """Format programs list as plain text"""
        if not programs:
            return ""
        
        text = "\nProgramas Recomendados:\n"
        for i, program in enumerate(programs[:3], 1):
            program_name = program.get("program_name", "Programa")
            score = program.get("score", 0)
            text += f"\n{i}. {program_name} (Afinidad: {score}/100)\n"
        return text


# Singleton instance
_email_service_instance = None

def get_email_service() -> EmailService:
    """Get singleton instance of EmailService"""
    global _email_service_instance
    if _email_service_instance is None:
        _email_service_instance = EmailService()
    return _email_service_instance




