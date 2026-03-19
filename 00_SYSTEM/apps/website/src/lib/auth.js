import CredentialsProvider from 'next-auth/providers/credentials';

/**
 * NextAuth.js configuration for LitigationOS.
 * Skeleton using credentials provider — swap in real DB lookups + bcrypt
 * once user table is provisioned.
 */
export const authOptions = {
  providers: [
    CredentialsProvider({
      name: 'Email',
      credentials: {
        email: { label: 'Email', type: 'email', placeholder: 'you@example.com' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        // TODO: replace with real DB lookup + bcrypt.compare
        // Example:
        //   const user = db.prepare('SELECT * FROM users WHERE email = ?').get(credentials.email);
        //   if (user && await bcrypt.compare(credentials.password, user.password_hash)) {
        //     return { id: user.id, email: user.email, name: user.name, tier: user.tier };
        //   }
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        // Skeleton: accept any login and return a stub user
        // Remove this block when real auth is wired up
        return {
          id: 'stub-user-id',
          email: credentials.email,
          name: credentials.email.split('@')[0],
          tier: 'free',
        };
      },
    }),
  ],

  session: { strategy: 'jwt', maxAge: 30 * 24 * 60 * 60 }, // 30 days

  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.tier = user.tier || 'free';
        token.userId = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      session.user.tier = token.tier;
      session.user.id = token.userId;
      return session;
    },
  },

  pages: {
    signIn: '/auth/login',
    newUser: '/auth/signup',
  },

  secret: process.env.NEXTAUTH_SECRET || 'litigationos-dev-secret-change-me',
};
