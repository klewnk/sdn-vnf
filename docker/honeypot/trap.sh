#!/bin/bash
# Ορίζουμε πού θα αποθηκεύεται το log τοπικά
LOG_FILE="/app/honeypot.log"

echo "Το VNF Honeypot ξεκίνησε! Ακούει σιωπηλά στην πόρτα 23..."

# 1. Συνδέουμε το Honeypot με το MinIO Edge Cloud (Βάζουμε IP 10.0.0.70)
mc alias set myminio http://minio:9000 kleon kleonpass

while true; do
  # 2. Περιμένει κάποιον να χτυπήσει την πόρτα 23...
  echo -e "Ubuntu 22.04 LTS\nLogin: " | nc -l -p 23 -q 1
  
  # 3. Μόλις κάποιος μπει, γράφει την ώρα και το γεγονός στο αρχείο
  echo "[$(date)] ⚠️ SECURITY ALERT: Κάποιος χτύπησε την παγίδα!" >> $LOG_FILE
  
  # 4. Στέλνει ΑΜΕΣΩΣ το αρχείο στο Storage (στο bucket mysite)
  mc cp $LOG_FILE myminio/mysite/honeypot_alerts.log
  
  echo "Επιτυχία! Το log μόλις στάλθηκε στο Edge Storage."
done