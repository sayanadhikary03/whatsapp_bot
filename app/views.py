import logging
import json

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse

from .decorators.security import signature_required
from .utils.whatsapp_utils import (
    process_whatsapp_message,
    is_valid_whatsapp_message,
)
from .config import config

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint - Welcome message"""
    return {"message": "Hello World"}


async def handle_message(body: dict):
    """
    Handle incoming webhook events from the WhatsApp API.

    This function processes incoming WhatsApp messages and other events,
    such as delivery statuses. If the event is a valid message, it gets
    processed. If the incoming payload is not a recognized WhatsApp event,
    an error is returned.

    Every message send will trigger 4 HTTP requests to your webhook: message, sent, delivered, read.

    Returns:
        response: A JSON response with appropriate HTTP status code.
    """
    # logging.info(f"request body: {body}")

    # Check if it's a WhatsApp status update
    if (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    ):
        logging.info("Received a WhatsApp status update.")
        return JSONResponse(content={"status": "ok"}, status_code=200)

    try:
        if is_valid_whatsapp_message(body):
            process_whatsapp_message(body)
            return JSONResponse(content={"status": "ok"}, status_code=200)
        else:
            # if the request is not a WhatsApp API event, return an error
            raise HTTPException(
                status_code=404,
                detail="Not a WhatsApp API event"
            )
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON")
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON provided"
        )


# Required webhook verifictaion for WhatsApp
@router.get("/webhook")
async def webhook_get(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    """
    Verify webhook endpoint for WhatsApp.
    """
    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == "subscribe" and token == config.VERIFY_TOKEN:
            # Respond with 200 OK and challenge token from the request
            logging.info("WEBHOOK_VERIFIED")
            return PlainTextResponse(content=challenge, status_code=200)
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            logging.info("VERIFICATION_FAILED")
            raise HTTPException(
                status_code=403,
                detail="Verification failed"
            )
    else:
        # Responds with '400 Bad Request' if verify tokens do not match
        logging.info("MISSING_PARAMETER")
        raise HTTPException(
            status_code=400,
            detail="Missing parameters"
        )


@router.post("/webhook")
@signature_required
async def webhook_post(request: Request):
    """
    Handle incoming webhook POST requests from WhatsApp.
    """
    # Get body from request state (stored by decorator)
    import json
    body = json.loads(request.state.body)
    print(body)
    return await handle_message(body)
