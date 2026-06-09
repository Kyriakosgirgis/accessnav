[app]

# (str) Title of your application
title = AccessNav

# (str) Package name
package.name = accessnav

# (str) Package domain
package.domain = org.accessnav

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,jpeg,kv,atlas,html,js,css,json

# (list) Source directories to exclude
source.exclude_dirs = venv,.venv,__pycache__,bin,.git

# (str) Application version
version = 0.1

# (list) Application requirements
requirements = python3,kivy,kivymd,plyer,pyjnius

# (list) Supported orientations
orientation = portrait

# (bool) Fullscreen
fullscreen = 1

# -------------------------------------------------- #
# Android
# -------------------------------------------------- #

# Permissions
android.permissions = CAMERA,INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

# Android API
android.api = 33
android.minapi = 24

# NDK
android.ndk = 25b

# Accept licenses automatically
android.accept_sdk_license = True

# Android architectures
android.archs = arm64-v8a, armeabi-v7a

# Copy python libs instead of libpymodules
android.copy_libs = 1

# Enable backup
android.allow_backup = True

# Debug artifact
android.debug_artifact = apk

# Release artifact
android.release_artifact = apk

# Entry point
android.entrypoint = org.kivy.android.PythonActivity

# Theme
android.apptheme = "@android:style/Theme.NoTitleBar.Fullscreen"

# Keep screen on
android.wakelock = True

# -------------------------------------------------- #
# iOS
# -------------------------------------------------- #

ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master

ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.10.0

ios.codesign.allowed = false

# -------------------------------------------------- #
# Buildozer
# -------------------------------------------------- #

[buildozer]

# Log level
log_level = 2

# Warn on root
warn_on_root = 1