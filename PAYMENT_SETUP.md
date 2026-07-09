# 💳 Payment Methods Setup Guide

This guide will help you set up multiple payment methods for your EbookGuy Bot premium system.

## Overview

The bot now supports **5 payment methods**:
1. ⭐ **Telegram Stars** (Built-in, recommended)
2. 💳 **PayPal**
3. 🏦 **UPI** (India)
4. ₿ **Cryptocurrency** (Bitcoin/Ethereum)
5. 💰 **Credit/Debit Cards** (via Stripe)

## Configuration

All payment settings are configured in **`info.py`** and can be managed via environment variables.

### 1. Telegram Stars (Built-in)

**Status:** ✅ Already implemented and active

**Features:**
- Native Telegram payment system
- Instant activation
- No external setup needed
- Best user experience

**Configuration:**
```env
TELEGRAM_STARS_ENABLED=True
```

**Prices are set in `PREMIUM_PRICES` dict in info.py:**
```python
PREMIUM_PRICES = {
    1: 11,      # 1 Day - 11 Stars
    7: 60,      # 7 Days - 60 Stars
    15: 110,    # 15 Days - 110 Stars
    30: 185,    # 30 Days - 185 Stars
    60: 340,    # 60 Days - 340 Stars
    90: 480,    # 90 Days - 480 Stars
}
```

---

### 2. PayPal Setup

**Step 1:** Create a PayPal Business Account
- Go to https://www.paypal.com/business
- Sign up and verify your account
- Note your email (e.g., `business@paypal.com`)

**Step 2:** Enable in Bot
```env
PAYPAL_ENABLED=True
PAYPAL_ID=business@paypal.com
```

**Step 3:** Testing
- When user selects PayPal, they'll see your PayPal ID
- They send payment via PayPal.me link
- They forward receipt to your support account
- Admin manually activates premium using `/addpremium <user_id> <days>`

**Payment Flow:**
```
User clicks "Pay with PayPal" 
  ↓
Redirected to PayPal.me link
  ↓
Completes payment
  ↓
Sends receipt to your support account
  ↓
You verify & run: /addpremium {user_id} {days}
  ↓
Premium activated
```

---

### 3. UPI Setup (India)

**Step 1:** Get your UPI ID
- Available from any major bank in India
- Format: `yourname@bankname` (e.g., `john@okhdfcbank`)
- No special account needed

**Step 2:** Enable in Bot
```env
UPI_ENABLED=True
UPI_ID=yourname@bankname
```

**Step 3:** Testing
- When user selects UPI, they see a payment link
- Clicking button opens their UPI app automatically
- They send payment using their preferred UPI app
- Forward receipt for verification

**Payment Flow:**
```
User clicks "Pay with UPI"
  ↓
UPI app opens automatically with payment details
  ↓
User completes payment
  ↓
Sends receipt to support
  ↓
You verify & run: /addpremium {user_id} {days}
  ↓
Premium activated
```

---

### 4. Cryptocurrency Setup

**Step 1:** Create Crypto Wallet
- **Bitcoin:** Use Coinbase, Kraken, or any BTC wallet
- **Ethereum:** MetaMask or any ETH wallet
- Keep your wallet address (public key) handy

**Step 2:** Enable in Bot
```env
CRYPTO_ENABLED=True
CRYPTO_WALLET=your_wallet_address
CRYPTO_TYPE=bitcoin    # or ethereum
```

**Example:**
```env
CRYPTO_WALLET=1A1z7agoat5w2BgUtiMB6triCqWTiAQWP
CRYPTO_TYPE=bitcoin
```

**Step 3:** Pricing
Default USD pricing for crypto:
```python
PAYMENT_PRICES_USD = {
    1: 1.99,
    7: 10.99,
    15: 19.99,
    30: 35.99,
    60: 65.99,
    90: 95.99,
}
```

**Payment Flow:**
```
User clicks "Pay with Crypto"
  ↓
Sees wallet address
  ↓
Sends crypto to wallet
  ↓
Sends transaction hash to support
  ↓
You verify on blockchain
  ↓
Run: /addpremium {user_id} {days}
  ↓
Premium activated
```

---

### 5. Credit/Debit Cards (Stripe)

**Step 1:** Create Stripe Account
- Go to https://stripe.com
- Sign up and complete verification
- Note your API keys

**Step 2:** Enable in Bot
```env
CARDS_ENABLED=True
STRIPE_API_KEY=sk_live_your_stripe_key
```

**Step 3:** Set Up Payment Page
- Create a Stripe payment link or embed checkout
- Update the payment button URL in `send_card_payment_link()` function
- Replace: `https://example.com/payment` with your actual Stripe link

**Payment Flow:**
```
User clicks "Pay with Card"
  ↓
Redirected to Stripe checkout
  ↓
Enters card details securely
  ↓
Payment processed immediately
  ↓
Webhook triggers premium activation
  ↓
User notified automatically
```

---

## Configuration Examples

### Example 1: All Methods Enabled
```env
TELEGRAM_STARS_ENABLED=True
PAYPAL_ENABLED=True
PAYPAL_ID=business@paypal.com

UPI_ENABLED=True
UPI_ID=john@okhdfcbank

CRYPTO_ENABLED=True
CRYPTO_WALLET=1A1z7agoat5w2BgUtiMB6triCqWTiAQWP
CRYPTO_TYPE=bitcoin

CARDS_ENABLED=True
STRIPE_API_KEY=sk_live_abc123...
```

### Example 2: Telegram Stars + PayPal Only
```env
TELEGRAM_STARS_ENABLED=True
PAYPAL_ENABLED=True
PAYPAL_ID=business@paypal.com

UPI_ENABLED=False
CRYPTO_ENABLED=False
CARDS_ENABLED=False
```

### Example 3: India-Focused (Stars + UPI)
```env
TELEGRAM_STARS_ENABLED=True
UPI_ENABLED=True
UPI_ID=yourname@bankname

PAYPAL_ENABLED=False
CRYPTO_ENABLED=False
CARDS_ENABLED=False
```

---

## User-Facing Messages

Update these in **`Script.py`** to customize payment messages:

```python
# Contact Information
OWNER = "YourOwnerUsername"           # Your Telegram username for payment support
SUPPORT_USERNAME = "YourSupportUsername"  # Support team username
```

---

## Admin Commands

### Activate Premium (Manual)
```
/addpremium <user_id> <days>
/addpremium 123456789 30
```

### Remove Premium
```
/removepremium <user_id>
/removepremium 123456789
```

### View Premium Users
```
/premiumusers
```

### Check Star Balance
```
/stars
```

### View Star Transactions
```
/starhistory [limit]
/starhistory 25
```

---

## Payment Verification Workflow

### For Manual Payment Methods (PayPal, UPI, Crypto)

1. **User sends payment** → Receives instruction page with your details
2. **User forwards receipt** → Sends to your support account
3. **You verify payment** → Check amount and transaction ID
4. **Activate premium** → Use `/addpremium` command
5. **Notify user** → User receives confirmation

---

## Security Best Practices

1. **Never share private keys** - Keep crypto wallets secure
2. **Use environment variables** - Don't hardcode sensitive data in code
3. **Verify payments** - Always check blockchain/payment gateway for crypto
4. **Log transactions** - Keep records for auditing
5. **Use HTTPS** - For all external payment links
6. **Set withdrawal limits** - Protect PayPal/crypto accounts

---

## Troubleshooting

### Issue: Button showing for disabled payment method
**Solution:** Make sure environment variable is set to `False`
```env
PAYPAL_ENABLED=False
```

### Issue: UPI link not opening
**Solution:** UPI links only work on Android devices with UPI app installed

### Issue: Crypto wallet not showing
**Solution:** Verify `CRYPTO_WALLET` is valid address format

### Issue: Users can't find payment button
**Solution:** Check that at least one payment method is `ENABLED=True`

---

## Customization

### Change Payment Prices
Edit `PAYMENT_PRICES_USD` in `info.py`:
```python
PAYMENT_PRICES_USD = {
    1: 0.99,      # Custom: 1 day
    7: 5.99,      # Custom: 1 week
    30: 19.99,    # Custom: 1 month
}
```

### Add New Payment Method
1. Add configuration in `info.py`
2. Create payment handler in `premium.py`
3. Add UI button in `get_payment_method_buttons()`
4. Add messages in `Script.py`

### Customize Payment Message
Edit `Script.py` - all payment messages are customizable:
```python
PAYPAL_PAYMENT = """Your custom message here"""
```

---

## Support

If users have payment issues:
- Provide clear instructions with their User ID
- Keep transaction records for disputes
- Test all payment methods regularly
- Have a support contact available 24/7

---

## Next Steps

1. ✅ Choose which payment methods to enable
2. ✅ Set environment variables in `.env` or deployment platform
3. ✅ Update `Script.py` with your contact information
4. ✅ Test each payment method thoroughly
5. ✅ Notify users about available payment options
6. ✅ Train support team on verification process

---

**Last Updated:** January 21, 2026  
**Version:** 1.0
