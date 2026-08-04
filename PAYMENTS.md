# Payments and Premium

The bot supports native Telegram Stars purchases and an optional link to an
external payment portal. Telegram Stars purchases are fulfilled automatically.
Payments made through an external portal require a separate verification
process and manual Premium activation.

## User Flow

1. The user sends `/plan`.
2. The bot displays the configured 30-day and 90-day plans.
3. The user selects a plan.
4. The bot displays available payment methods.
5. Telegram Stars opens a native Telegram invoice.
6. A configured external portal opens in the user's browser.

The external portal button appears only when `PAYMENT_WEBSITE` starts with
`https://` or `http://`.

## Telegram Stars Flow

### Invoice creation

When the user confirms a plan, the bot:

1. Loads the current global Premium settings.
2. Confirms that Premium purchases and Stars payments are enabled.
3. Reads the current Stars price for the selected plan.
4. Creates an `XTR` invoice tied to the user's Telegram ID.
5. Encodes the plan, user ID, and expected price in the invoice payload.

Only the configured 30-day and 90-day plans are accepted.

### Pre-checkout validation

Before Telegram completes payment, the bot verifies:

- Premium purchases are still enabled
- Telegram Stars payments are still enabled
- The plan is recognized
- The invoice user matches the paying user
- The currency is `XTR`
- The amount matches the current configured Stars price
- The encoded invoice price has not been changed

Failed validation rejects checkout without activating Premium.

### Successful payment

After Telegram reports a successful charge, the bot:

1. Revalidates the user, amount, currency, plan, and charge ID.
2. Registers the Telegram charge in MongoDB.
3. Applies or extends Premium exactly once.
4. Stores the activation result and expiry.
5. Sends a confirmation message to the user.

The Telegram payment charge ID is the idempotency key. Reprocessing the same
successful-payment update does not extend Premium twice.

## External Payment Portal

Set:

```dotenv
PAYMENT_WEBSITE=https://payments.example.com/
```

The bot does not collect, verify, or fulfill UPI, Google Pay, PayPal, Binance,
crypto, or card payments itself. Those methods may be displayed and processed
by the configured external website.

After independently verifying an external payment, an administrator can grant
Premium manually:

```text
/addpremium <user_id> <days>
```

Example:

```text
/addpremium 123456789 30
```

Do not grant Premium from a screenshot alone. Verify the transaction in the
payment provider's own dashboard.

## Runtime Settings

Open `/settings`, then select the Premium category.

Relevant settings include:

| Setting | Purpose |
| --- | --- |
| Premium purchases | Enables or disables all purchase entry points |
| Telegram Stars payments | Enables or disables Stars invoices |
| 30-day Stars price | Stars charged for a 30-day plan |
| 90-day Stars price | Stars charged for a 90-day plan |
| 30-day INR price | Informational portal price shown in the bot |
| 90-day INR price | Informational portal price shown in the bot |
| Premium downloads per day | Premium daily download allowance |
| Premium download cooldown | Delay between Premium downloads |
| Premium maximum file size | Premium delivery size restriction |
| Premium conversions per day | Premium conversion allowance |

Settings stored through `/settings` apply without restarting the bot.

## Environment Configuration

| Variable | Required | Purpose |
| --- | --- | --- |
| `PAYMENT_WEBSITE` | No | Optional external portal URL |
| `BOT_TOKEN` | Yes | Required for Telegram invoices and bot operation |
| `DATABASE_URI` | Yes | Stores users, Premium state, and payment records |
| `ADMINS` | Yes | Controls access to Premium administration commands |

Legacy environment values such as `PAYPAL_ID`, `UPI_ID`, `CRYPTO_WALLET`, and
`BINANCE_PAY_ID` are not used by the current in-bot payment flow. Configure
those payment details on the external portal instead.

## User Commands

| Command | Description |
| --- | --- |
| `/plan` | View Premium plans and begin payment |
| `/mystatus` | View Premium expiry and remaining limits |

## Administrator Commands

| Command | Description |
| --- | --- |
| `/addpremium <user_id> <days>` | Grant or extend Premium manually |
| `/removepremium <user_id>` | Remove Premium |
| `/premiumusers` | List Premium users |
| `/stars` | Display the bot's Telegram Stars balance |
| `/starhistory [limit]` | Display recorded Stars transactions |
| `/settings` | Change Premium availability, prices, and limits |

## Data Recorded for Stars Payments

The payment store records:

- Telegram payment charge ID
- Provider payment charge ID when supplied
- Telegram user ID
- Plan duration
- Stars paid
- Currency
- Invoice payload
- Fulfillment status
- Premium expiry and activation timestamps
- Last processing error when fulfillment fails

Do not log bot tokens, MongoDB credentials, or raw user payment credentials.

## Disabling Payments

To disable all new Premium purchases:

1. Open `/settings`.
2. Open Premium.
3. Disable Premium purchases.

To disable only Telegram Stars while retaining the external portal:

1. Leave Premium purchases enabled.
2. Disable Telegram Stars payments.
3. Ensure `PAYMENT_WEBSITE` contains a valid URL.

Disabling purchases does not remove Premium from existing users.

## Testing

Automated tests cover:

- Invoice payload parsing
- Unknown-plan rejection
- Price-change rejection
- Pre-checkout acceptance and rejection
- Successful-payment amount validation
- Idempotent Premium fulfillment
- External portal button visibility

Run:

```bash
python -m unittest discover -s tests -v
```

Before production release, manually test:

- `/plan` with both plan durations
- Stars invoice creation
- Cancelled checkout
- Successful checkout
- Repeated successful-payment delivery
- `/mystatus` after payment
- Purchase and Stars feature toggles
- External portal shown and hidden states
- Manual Premium activation

## Troubleshooting

### `/plan` does not offer payment

Confirm that Premium purchases are enabled in `/settings`.

### Telegram Stars button is missing

Confirm that Telegram Stars payments are enabled and that the selected plan has
a non-zero Stars price.

### External portal button is missing

Set `PAYMENT_WEBSITE` to a complete URL beginning with `https://` or `http://`.

### Checkout says the payment request is invalid

The plan price or payment settings may have changed after the invoice was
created. Return to `/plan` and create a new invoice.

### User paid but Premium was not activated

Check application logs and `/starhistory`. Do not blindly reapply Premium until
the Telegram charge ID and stored fulfillment status have been verified.

### External payment was completed

Verify it directly with the provider, identify the correct Telegram user ID,
and use `/addpremium`.
