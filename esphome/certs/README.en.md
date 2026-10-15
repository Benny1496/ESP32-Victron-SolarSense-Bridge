# Trusted Cerbo certificate

Users must provide their own trusted public CA/server certificate as `cerbo-ca.pem` (PEM). **Never use a private key.** The certificate identity must match the hostname in `cerbo_https_url`. ESPHome supports self-signed and private-CA server certificates via `http_request.ca_certificate_path`. Never disable certificate verification. This file is site-specific and must not be committed. Merely downloading a certificate over an untrusted connection does not establish authenticity.
