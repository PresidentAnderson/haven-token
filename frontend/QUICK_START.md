# HAVEN Token Frontend - Quick Start

## 5-Minute Setup

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Configure Environment
```bash
cp .env.example .env.local
```

Edit `.env.local` and add your WalletConnect Project ID:
```env
NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=your_project_id_here
```

Get your Project ID: [cloud.walletconnect.com](https://cloud.walletconnect.com)

### 3. Run Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

That's it! 🎉

---

## Common Commands

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Check TypeScript
```

---

## File Structure Quick Reference

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Main landing page
│   ├── providers.tsx       # Web3 providers
│   └── globals.css         # Tailwind styles
├── components/
│   ├── Navigation.tsx      # Top nav
│   ├── Hero.tsx           # Hero section
│   ├── HowItWorks.tsx     # Process section
│   ├── Tokenomics.tsx     # Charts & calculator
│   ├── FAQ.tsx            # FAQ accordion
│   └── Footer.tsx         # Footer
├── lib/
│   ├── wagmi.ts           # Web3 config
│   ├── contracts.ts       # Contract ABIs
│   ├── constants.ts       # App constants
│   └── utils.ts           # Helpers
└── .env.local             # Your config (create this!)
```

---

## Environment Variables

### Required
```env
NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=xxx
```

### Optional (for production)
```env
NEXT_PUBLIC_ALCHEMY_API_KEY=xxx
NEXT_PUBLIC_HAVEN_CONTRACT_ADDRESS=0x...
NEXT_PUBLIC_HAVEN_CONTRACT_ADDRESS_TESTNET=0x...
```

---

## Deploy to Vercel

1. Push code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Click "Import Project"
4. Select your repository
5. Add environment variables
6. Click "Deploy"

Done! ✅

---

## Customization Quick Guide

### Change Colors
Edit `tailwind.config.ts`:
```typescript
colors: {
  primary: { ... },    // Main brand color
  secondary: { ... },  // Accent color
  accent: { ... },     // Special elements
}
```

### Update Content
Edit `lib/constants.ts`:
```typescript
TOKEN_CONSTANTS      // Token info
REWARD_RATES         // Staking, booking rates
FAQ_ITEMS            // FAQ questions
HOW_IT_WORKS_STEPS   // Process steps
```

### Add Contract Address
Edit `.env.local`:
```env
NEXT_PUBLIC_HAVEN_CONTRACT_ADDRESS=0xYourAddress
```

---

## Troubleshooting

### "Module not found"
```bash
rm -rf node_modules .next
npm install
```

### Wallet won't connect
- Check WalletConnect Project ID is set
- Try different wallet (MetaMask)
- Clear browser cache

### Build fails
```bash
npm run type-check  # See TypeScript errors
npm run lint        # See linting errors
```

---

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure environment
3. ✅ Run locally
4. 📝 Update content/branding
5. 🚀 Deploy to production
6. 🔗 Connect your contract

---

## Documentation

- **Full Docs:** `README.md`
- **Setup Guide:** `SETUP.md`
- **Features:** `FEATURES.md`
- **Summary:** `PROJECT_SUMMARY.md`

---

## Support

- 📚 [Next.js Docs](https://nextjs.org/docs)
- 🌐 [Wagmi Docs](https://wagmi.sh)
- 💬 Discord: Community support
- 🐛 GitHub Issues: Bug reports

---

**Built with Next.js 14 + TypeScript + TailwindCSS + Wagmi**

Made with ❤️ for the Puerto Vallarta Tribe community
