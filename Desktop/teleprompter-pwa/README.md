# Teleprompter PWA

A Progressive Web App (PWA) teleprompter application that works on desktop and iOS devices. Perfect for presentations, speeches, and video recording with auto-scrolling text.

## Features

✨ **Progressive Web App** - Works offline with Service Worker support
📱 **Cross-Platform** - Runs on web browsers and iOS (via Capacitor)
🎯 **Auto-Scroll** - Adjustable scrolling speed for hands-free reading
🎨 **Clean UI** - Minimalist design focused on readability
⚡ **Fast & Responsive** - Instant loading and smooth performance
📝 **Text Control** - Easy text input and real-time updates

## Quick Start

### Web Version

1. Clone the repository:
```bash
git clone https://github.com/hafsaghannaj/telepromoter-pwa.git
cd telepromoter-pwa
```

2. Open `index.html` in your web browser or serve it locally:
```bash
npx http-server
```

3. Visit `http://localhost:8080` in your browser

### iOS Version

1. Install dependencies:
```bash
npm install
```

2. Build and run on iOS:
```bash
npm run build
npx cap add ios
npx cap sync
npx cap open ios
```

## Project Structure

```
teleprompter-pwa/
├── index.html           # Main HTML file
├── app.js              # Core application logic
├── styles.css          # Application styling
├── sw.js               # Service Worker for offline support
├── manifest.webmanifest # PWA manifest configuration
├── package.json        # Dependencies and scripts
├── capacitor.config.json # Capacitor iOS configuration
├── www/                # Built web files
├── ios/                # iOS native project
└── scripts/            # Build scripts
```

## Usage

1. Paste or type your speech/script into the text area
2. Click "Start" to begin the teleprompter
3. Adjust the scroll speed with the slider
4. Use pause/resume controls as needed
5. The app will automatically scroll through your text

## Development

### Dependencies

- **Capacitor** - For iOS native functionality
- Service Worker API - For offline support

### Building

```bash
npm run build
```

### Deploying

The app is ready to deploy to any static hosting service (GitHub Pages, Netlify, Vercel, etc.)

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- iOS Safari (via Capacitor)

## License

MIT

## Author

Hafsa Ghannaj

---

Made with ❤️ for better presentations
