# DailyFluent Mobile App

Flutter mobile application for DailyFluent - Language learning platform.

## Getting Started

### Prerequisites
- Flutter SDK >= 3.2.0
- Dart >= 3.2.0
- Android Studio (for Android) / Xcode (for iOS)

### Setup

```bash
# Install dependencies
flutter pub get

# Run on device/emulator
flutter run

# Run on specific platform
flutter run -d android
flutter run -d ios
flutter run -d chrome
```

### Project Structure

```
lib/
├── main.dart                 # Entry point
├── app.dart                  # MaterialApp + GoRouter + Theme
├── core/
│   ├── api/                  # Dio HTTP client + JWT auth
│   ├── router/               # GoRouter configuration
│   ├── storage/              # Secure token storage
│   └── theme/                # Material 3 theme system
├── features/
│   ├── auth/                 # Login, Signup, JWT management
│   ├── home/                 # Dashboard, tab screens
│   ├── kanji/                # Kanji learning (JLPT)
│   ├── vocab/                # Vocabulary courses & flashcards
│   ├── grammar/              # Grammar points & exercises
│   ├── exam/                 # Exams (TOEIC, JLPT, English)
│   ├── streak/               # Study streak tracking
│   ├── video/                # Video lessons
│   ├── ebook/                # E-book reader
│   ├── placement/            # Placement test
│   ├── shop/                 # Item shop
│   ├── wallet/               # Wallet management
│   ├── notifications/        # Push notifications
│   ├── profile/              # User profile
│   └── settings/             # App settings
└── shared/
    ├── widgets/              # Reusable UI components
    └── utils/                # Utility functions
```

### Architecture

- **State Management**: Riverpod 2.x
- **HTTP Client**: Dio with auto JWT refresh
- **Routing**: go_router with auth guards
- **Storage**: flutter_secure_storage for tokens
