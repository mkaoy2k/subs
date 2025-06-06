# Ping Operations server
# OPS_SVR="https://bold-squirrel-vertically.ngrok-free.app"
OPS_SVR="http://127.0.0.1:8501"
while true
    do 
        echo "================================================"
        echo "ping $OPS_SVR/about ..."
        curl "$OPS_SVR/about"
        echo $(date +%m/%d/%y-%H:%M:%S)
        # Sleep for a random duration between 1 to 3 minutes (60-180 seconds)
        echo "Sleep for a random duration between 1 to 3 minutes (60-180 seconds) ..."
        sleep $((60 + RANDOM % 121))
 
        echo "================================================"
        echo "ping $OPS_SVR/faq..."
        curl "$OPS_SVR/faq"
        echo $(date +%m/%d/%y-%H:%M:%S)
        # Sleep for a random duration between 1 to 3 minutes (60-180 seconds)
        echo "Sleep for a random duration between 1 to 3 minutes (60-180 seconds) ..."
        sleep $((60 + RANDOM % 121))

    done    
