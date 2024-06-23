export PROD="$HOME/My_Prods/FamilyTrees"
echo "================================================"
echo "--- Push FamilyTrees to Production ---"
echo "===> From: $PWD"
echo "===> To: $PROD"

# initialize directories
echo "================================================"
echo "===> initialize directories if not exists..."
if [ -d "$PROD" ]; then
    chmod 0755 $PROD
else
    mkdir -v -m 0755 $PROD
fi

if [ -d "$PROD/data" ]; then
    chmod 0755 $PROD/data
else
    mkdir -v -m 0755 $PROD/data
fi

if [ -d "$PROD/static" ]; then
    chmod 0755 $PROD/static
else
    mkdir -v -m 0755 $PROD/static
fi

if [ -d "$PROD/templates" ]; then
    chmod 0755 $PROD/templates
else
    mkdir -v -m 0755 $PROD/templates
fi

# push config 
echo "================================================"
echo "===> push config ..."
cp -fpv template.csv $PROD/data
cp -fpv template.env.txt $PROD/.env
cp -fpv template.gitignore.txt $PROD/.gitignore
cp -fpv L10N.json $PROD
cp -fpv L10N_TW.json $PROD
cp -fpv L10N_US.json $PROD
cp -fpv ops_menu.json $PROD

# push Python files
echo "================================================"
echo "===> push Python files ..."
cp -fpv db_deta.py $PROD
cp -fpv db_sqlite.py $PROD
cp -fpv family.py $PROD
cp -fpv family_pe.py $PROD
cp -fpv funcUtils.py $PROD
cp -fpv glogTime.py $PROD
cp -fpv htmlUtils.py $PROD
cp -fpv ops_activate.py $PROD
cp -fpv ops_db_insert.py $PROD
cp -fpv ops_db_query.py $PROD
cp -fpv ops_db_update.py $PROD
cp -fpv ops_svr.py $PROD
cp -fpv sdb_deta.py $PROD
cp -fpv sdb_sqlite.py $PROD

# push docs
echo "================================================"
echo "===> push docs ..."
cp -fpv README.md $PROD
cp -fpv requirements.txt $PROD
cp -fpv environment.yaml $PROD

# push html/templates
echo "================================================"
echo "===> push html ..."
cp -fpv static/main.css $PROD/static
cp -fpv static/mkao2019.jpeg $PROD/static
cp -fpv static/ScreenShot_charge.png $PROD/static
cp -fpv static/ScreenShot_cookie_manager.png $PROD/static
cp -fpv static/ScreenShot_creator.png $PROD/static
cp -fpv static/ScreenShot_donate.png $PROD/static
cp -fpv static/ScreenShot_login.png $PROD/static
cp -fpv static/ScreenShot_resetPW.png $PROD/static
cp -fpv static/ScreenShot_settings.png $PROD/static
cp -fpv static/ScreenShot_signup.png $PROD/static
cp -fpv templates/about.html $PROD/templates
cp -fpv templates/layout.html $PROD/templates
cp -fpv templates/faq.html $PROD/templates

# set file modes
echo "================================================"
echo "===> set file modes ..."
cd $PROD
chmod 755 .*
chmod 755 *
chmod 755 data
chmod 644 data/*.csv
chmod 644 data/users.db
chmod 755 static
chmod 755 templates
chmod 644 .env
chmod 644 .gitignore
chmod 644 README.md
chmod 644 requirements.txt
chmod 644 environment.yaml

echo $(date +%m/%d/%y-%H:%M:%S)
echo "Done."
echo "================================================"