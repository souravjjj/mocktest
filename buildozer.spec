[app]
title = Online Mock Test
package.name = mocktest
package.domain = org.mocktest

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf
source.exclude_dirs = .github,.git,bin,.buildozer,__pycache__

version = 1.0
requirements = python3,kivy==2.3.0

orientation = portrait
fullscreen = 0

android.permissions =
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
