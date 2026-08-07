# Payments and Premium

The bot supports native Telegram Stars purchases, Google Pay / UPI payment
details, direct Binance Pay links, and an optional external payment portal
fallback. Telegram Stars purchases are fulfilled automatically. Manual and
portal payments require verification and Premium activation.

## User Flow

1. The user sends `/plan`.
2. The bot displays the configured 30-day and 90-day plans.
3. The user selects a plan.
4. The bot displays configured payment methods.
5. Telegram Stars opens a native Telegram invoice.
6. Google Pay / UPI displays the configured payment details.
7. Binance Pay opens the configured HTTPS payment link.
8. `I Have Paid` displays proof submission instructions.

If no direct manual method is configured, the external portal button appears
when `PAYMENT_WEBSITE` starts with `https://` or `http://`.

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

## Google Pay and UPI

The bot builds a UPI payment URI from the selected plan's INR price:

```dotenv
UPI_ID=merchant@bank
UPI_PAYEE_NAME=Example Merchant
```

Telegram rejects direct `upi://` inline button URLs as an unsupported protocol.
The bot catches that response, removes the Pay button, and shows the UPI ID and
amount for manual entry. A one-tap UPI action requires an HTTPS page that opens
the UPI URI after a user click.

The 30-day and 90-day INR amounts are controlled through `/settings`.

## Binance Pay

Configure one HTTPS payment link per plan:

```dotenv
BINANCE_PAY_ID=123456789
BINANCE_PAY_URL_30=https://s.binance.com/example30
BINANCE_PAY_URL_90=https://s.binance.com/example90
BINANCE_30_DAYS_USD=1.99
BINANCE_90_DAYS_USD=4.99
```

The displayed USD amounts are informational and must match the corresponding
Binance payment links.

## Manual Verification

After paying through UPI or Binance Pay, the user selects `I Have Paid`. The
bot displays the method, plan, amount, Telegram user ID, and a link to the
configured support destination.

An administrator must verify the provider transaction before using:

```text
/addpremium <user_id> <days>
```

Do not grant Premium from a screenshot alone. Verify the transaction in the
payment provider's own dashboard and ensure a transaction ID has not been
reused.

## External Payment Portal Fallback

Set:

```dotenv
PAYMENT_WEBSITE=https://payments.example.com/
```

The portal is shown only when no direct UPI or Binance method is available.
The bot does not automatically verify or fulfill payments completed through
the portal.

After independently verifying an external payment, an administrator can grant
Premium manually:

```text
/addpremium <user_id> <days>
```

Example:

```text
/addpremium 123456789 30
```

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
| `UPI_ID` | No | UPI virtual payment address |
| `UPI_PAYEE_NAME` | No | Payee name included in the UPI link |
| `BINANCE_PAY_ID` | No | Binance Pay recipient ID shown to users |
| `BINANCE_PAY_URL_30` | No | Binance HTTPS link for 30 days |
| `BINANCE_PAY_URL_90` | No | Binance HTTPS link for 90 days |
| `BINANCE_30_DAYS_USD` | No | Display amount for the 30-day link |
| `BINANCE_90_DAYS_USD` | No | Display amount for the 90-day link |
| `BOT_TOKEN` | Yes | Required for Telegram invoices and bot operation |
| `DATABASE_URI` | Yes | Stores users, Premium state, and payment records |
| `ADMINS` | Yes | Controls access to Premium administration commands |

Legacy values such as `PAYPAL_ID` and `CRYPTO_WALLET` are not used by the
current in-bot payment flow.

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
- UPI URI amount and payee construction
- Binance plan-to-link mapping
- Invalid Binance link rejection
- Direct UPI button rejection fallback

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
- UPI and Binance Pay detail pages
- Direct UPI behavior on Android, iOS, and Telegram Desktop
- External portal fallback shown and hidden states
- Manual Premium activation

## Troubleshooting

### `/plan` does not offer payment

Confirm that Premium purchases are enabled in `/settings`.

### Telegram Stars button is missing

Confirm that Telegram Stars payments are enabled and that the selected plan has
a non-zero Stars price.

### External portal button is missing

Set `PAYMENT_WEBSITE` to a complete URL beginning with `https://` or `http://`.

The portal is intentionally hidden when a direct UPI or Binance method is
configured.

### Google Pay button is missing

Set both `UPI_ID` and `UPI_PAYEE_NAME`, and configure a non-zero INR plan price
through `/settings`.

Administrators can also configure and enable UPI from `/settings` under
`Manual Payments`. Database values override the environment defaults.

### Direct UPI button is unavailable

Telegram rejected the `upi://` URL. Copy the displayed UPI ID and amount into
the payment app, or use an HTTPS redirect page for cross-client support.

### Binance Pay button is missing

Set the matching plan URL to a complete `https://` URL hosted by Binance.

Administrators can configure both Binance plan links, the displayed amounts,
and the optional Binance Pay ID from `/settings` under `Manual Payments`.
Database values override the environment defaults.

### Checkout says the payment request is invalid

The plan price or payment settings may have changed after the invoice was
created. Return to `/plan` and create a new invoice.

### User paid but Premium was not activated

Check application logs and `/starhistory`. Do not blindly reapply Premium until
the Telegram charge ID and stored fulfillment status have been verified.

### External payment was completed

Verify it directly with the provider, identify the correct Telegram user ID,
and use `/addpremium`.
