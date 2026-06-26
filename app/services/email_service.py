import os
import smtplib
import logging
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


async def send_intake_confirmation(cliente_email: str, detalle: dict) -> bool:
    """Envía email de confirmación de retiro. Fallo no rollbackea la transacción."""
    try:
        host = os.getenv("SMTP_HOST", "")
        port = int(os.getenv("SMTP_PORT", "587"))
        user = os.getenv("SMTP_USER", "")
        password = os.getenv("SMTP_PASS", "")

        if not host or not user:
            logger.warning("SMTP no configurado, email no enviado.")
            return False

        msg = MIMEText(f"Confirmación de ingreso a planta:\n{detalle}")
        msg["Subject"] = "BASA - Confirmación de Retiro"
        msg["From"] = user
        msg["To"] = cliente_email

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Error enviando email: {e}")
        return False
