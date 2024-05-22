:: generate new pvt key and cert
:: NB this is self signed, so will be rejected by Chrome
:: if you're doing UDP on the internet, gotta be paranoid!
openssl req -newkey rsa:2048 -nodes -keyout ..\cfg\certificate.key -x509 -out ..\cfg\certificate.pem -subj "/CN=Test Certificate" -addext "subjectAltName = DNS:localhost"
:: extract base64 fingerprint from the cert
openssl x509 -pubkey -noout -in ..\cfg\certificate.pem | openssl rsa -pubin -outform der | openssl dgst -sha256 -binary | openssl enc -base64