/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'sonora-cyan': '#00E7FF',
        'sonora-purple': '#9B4CFF',
        'sonora-dark': '#05040b',
        'sonora-darker': '#070617',
      },
      fontFamily: {
        'orbitron': ['Orbitron', 'monospace'],
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 20px #00E7FF' },
          '100%': { boxShadow: '0 0 30px #00E7FF, 0 0 40px #00E7FF' },
        }
      }
    },
  },
  plugins: [],
}



















