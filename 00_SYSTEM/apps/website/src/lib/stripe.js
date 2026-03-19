import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_placeholder');

/* ─── Tier Definitions ─── */
export const TIERS = {
  free: {
    name: 'Free',
    monthlyPrice: 0,
    annualPrice: 0,
    stripePriceMonthly: null,
    stripePriceAnnual: null,
    limits: { cases: 1, storage: '500MB', storageMB: 500 },
    features: [
      'Single case management',
      'Basic timeline view',
      'Document upload (500MB)',
      'Community support',
    ],
  },
  lite: {
    name: 'Lite',
    monthlyPrice: 2900,
    annualPrice: 23200,  // 20% off → $29 × 0.8 × 12
    stripePriceMonthly: process.env.STRIPE_PRICE_LITE_MONTHLY || null,
    stripePriceAnnual: process.env.STRIPE_PRICE_LITE_ANNUAL || null,
    limits: { cases: 1, storage: '5GB', storageMB: 5120 },
    features: [
      'Single case management',
      'OMEGA credibility scoring',
      'Evidence contradiction detection',
      'Document upload (5GB)',
      'Email support',
    ],
  },
  pro: {
    name: 'Pro',
    monthlyPrice: 9900,
    annualPrice: 79200,  // 20% off → $99 × 0.8 × 12
    stripePriceMonthly: process.env.STRIPE_PRICE_PRO_MONTHLY || null,
    stripePriceAnnual: process.env.STRIPE_PRICE_PRO_ANNUAL || null,
    limits: { cases: 5, storage: '25GB', storageMB: 25600 },
    features: [
      'Up to 5 cases',
      'Full AI analysis suite',
      'Relationship graph visualization',
      'Multi-forum filing support',
      'Court document generation',
      'Priority support',
    ],
  },
  enterprise: {
    name: 'Enterprise',
    monthlyPrice: 29900,
    annualPrice: 239200,  // 20% off → $299 × 0.8 × 12
    stripePriceMonthly: process.env.STRIPE_PRICE_ENT_MONTHLY || null,
    stripePriceAnnual: process.env.STRIPE_PRICE_ENT_ANNUAL || null,
    limits: { cases: -1, storage: '100GB', storageMB: 102400 },
    features: [
      'Unlimited cases',
      'Full REST API access',
      'White-label branding',
      'Custom integrations',
      'Dedicated account manager',
      'SSO & team management',
      '99.9% SLA',
    ],
  },
};

/* ─── Checkout Session ─── */
export async function createCheckoutSession(tier, email, billing = 'monthly') {
  const plan = TIERS[tier];
  if (!plan || tier === 'free') {
    throw new Error(`Invalid tier for checkout: ${tier}`);
  }

  const isAnnual = billing === 'annual';
  const priceId = isAnnual ? plan.stripePriceAnnual : plan.stripePriceMonthly;
  const amount = isAnnual ? plan.annualPrice : plan.monthlyPrice;
  const interval = isAnnual ? 'year' : 'month';

  const lineItems = priceId
    ? [{ price: priceId, quantity: 1 }]
    : [{
        price_data: {
          currency: 'usd',
          product_data: { name: `LitigationOS ${plan.name}` },
          unit_amount: isAnnual ? Math.round(plan.annualPrice / 12) : amount,
          recurring: { interval },
        },
        quantity: 1,
      }];

  const session = await stripe.checkout.sessions.create({
    payment_method_types: ['card'],
    mode: 'subscription',
    customer_email: email,
    line_items: lineItems,
    metadata: { tier, billing },
    success_url: `${process.env.NEXT_PUBLIC_URL || 'http://localhost:3000'}/dashboard?success=true&tier=${tier}`,
    cancel_url: `${process.env.NEXT_PUBLIC_URL || 'http://localhost:3000'}/pricing`,
  });

  return session;
}

/* ─── Customer Portal ─── */
export async function createPortalSession(customerId) {
  const session = await stripe.billingPortal.sessions.create({
    customer: customerId,
    return_url: `${process.env.NEXT_PUBLIC_URL || 'http://localhost:3000'}/dashboard`,
  });
  return session;
}

/* ─── Webhook Handler ─── */
export function handleWebhookEvent(event) {
  const handlers = {
    'checkout.session.completed': (data) => {
      const { customer_email, subscription, metadata } = data;
      console.log(`[Stripe] New subscription: ${customer_email} tier=${metadata?.tier}`);
      // TODO: upsert user record with tier + subscription ID
      return { action: 'subscription_created', email: customer_email, subscription, tier: metadata?.tier };
    },
    'customer.subscription.updated': (data) => {
      console.log(`[Stripe] Subscription updated: ${data.id} status=${data.status}`);
      // TODO: update user tier/status in DB
      return { action: 'subscription_updated', subscriptionId: data.id, status: data.status };
    },
    'customer.subscription.deleted': (data) => {
      console.log(`[Stripe] Subscription cancelled: ${data.id}`);
      // TODO: downgrade user to free tier
      return { action: 'subscription_cancelled', subscriptionId: data.id };
    },
    'invoice.payment_failed': (data) => {
      console.log(`[Stripe] Payment failed: ${data.customer_email}`);
      // TODO: notify user, set grace period
      return { action: 'payment_failed', email: data.customer_email };
    },
  };

  const handler = handlers[event.type];
  if (handler) {
    return handler(event.data.object);
  }
  console.log(`[Stripe] Unhandled event: ${event.type}`);
  return { action: 'unhandled', type: event.type };
}

export default stripe;
