#!/usr/bin/env bash
for H in encarparse.ozzy1986.com laravel.ozzy1986.com mvp-python-react.ozzy1986.com round.ozzy1986.com site-generator.ozzy1986.com wordpress.ozzy1986.com xsiblings.com www.xsiblings.com ozzb2b.com; do
  printf "=== %-42s http:  " "$H"
  curl -skI -H "Host: $H" http://127.0.0.1/  | head -n 1
  printf "=== %-42s https: " "$H"
  curl -skI --resolve "$H:443:127.0.0.1" "https://$H/" | head -n 1
done
