[app]
title = Minhas Financas
package.name = minhasfinancas
package.domain = org.minhasfinancas
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,sqlite3,charset-normalizer==3.3.2
orientation = portrait
fullscreen = 0
android.api = 34
android.minapi = 24
android.ndk = 27
android.archs = arm64-v8a
android.accept_sdk_license = True
android.private_storage = True
android.permissions = INTERNET
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1
