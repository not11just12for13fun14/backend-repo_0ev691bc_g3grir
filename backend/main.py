from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import stripe
from datetime import datetime

# Database helpers (pre-configured in environment)
from database import db, create_document, get_documents

app = FastAPI(title="Plasma Node API", version="1.0.0")

# CORS
frontend_url = os.getenv("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stripe setup (test mode)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_51M...replace_me...")


class CheckoutItem(BaseModel):
    name: str
    price_id: str
    quantity: int = 1


class CheckoutSessionRequest(BaseModel):
    items: List[CheckoutItem]
    success_url: str
    cancel_url: str
    customer_email: Optional[str] = None


class Lead(BaseModel):
    email: str
    plan: Optional[str] = None
    source: Optional[str] = None


@app.get("/")
async def root():
    return {"name": "Plasma Node API", "status": "ok", "time": datetime.utcnow().isoformat()}


@app.get("/test")
async def test():
    # Verify db connection by counting any collection
    try:
        docs = await get_documents("lead", {}, limit=1)
        return {"db": "ok", "count_sample": len(docs)}
    except Exception as e:
        return {"db": "error", "detail": str(e)}


@app.post("/leads")
async def create_lead(lead: Lead):
    data = lead.model_dump()
    doc = await create_document("lead", data)
    return {"ok": True, "lead": doc}


@app.post("/create-checkout-session")
async def create_checkout_session(payload: CheckoutSessionRequest):
    try:
        line_items = [
            {
                "price": item.price_id,
                "quantity": item.quantity,
            }
            for item in payload.items
        ]
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=line_items,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
            customer_email=payload.customer_email,
            billing_address_collection="auto",
            allow_promotion_codes=True,
            automatic_tax={"enabled": True},
        )
        return {"id": session["id"], "url": session["url"]}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create checkout session")
