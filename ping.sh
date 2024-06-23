OPS_SVR="https://sharp-planets-clean.loca.lt"
while true
    do 
        echo "================================================"
        echo "ping $OPS_SVR/about ..."
        curl "$OPS_SVR/about"
        echo "================================================"
        sleep 312
        echo "ping $OPS_SVR/faq..."
        curl "$OPS_SVR/faq"
        sleep 321
    done
