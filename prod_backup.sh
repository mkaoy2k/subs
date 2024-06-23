export PROD="$HOME/My_Prods/FamilyTrees"
export BACKUP="$HOME/mkao/My_Prods/FamilyTrees"
echo "================================================"
echo "--- Backup Production ---"
echo "===> From: $PWD"
echo "===> To: $BACKUP"

# initialize directories
echo "================================================"
echo "===> initialize directories ..."
if [ -d "$BACKUP" ]; then
    chmod 0755 $BACKUP
else
    mkdir -v -m 0755 $BACKUP
fi

if [ -d "$BACKUP/data" ]; then
    chmod 0755 $BACKUP/data
else
    mkdir -v -m 0755 $BACKUP/data
fi

if [ -d "$BACKUP/static" ]; then
    chmod 0755 $BACKUP/static
else
    mkdir -v -m 0755 $BACKUP/static
fi

if [ -d "$BACKUP/data" ]; then
    chmod 0755 $BACKUP/templates
else
    mkdir -v -m 0755 $BACKUP/templates
fi

# push config 
echo "================================================"
echo "===> push config ..."
cp -fpv data/template.csv $BACKUP/data
cp -fpv .env $BACKUP
cp -fpv .gitignore $BACKUP
cp -fpv L10N.json $BACKUP
cp -fpv L10N_TW.json $BACKUP
cp -fpv L10N_US.json $BACKUP
cp -fpv ops_menu.json $BACKUP

# push Python files
echo "================================================"
echo "===> push Python files ..."
cp -fpv db_deta.py $BACKUP
cp -fpv db_sqlite.py $BACKUP
cp -fpv family.py $BACKUP
cp -fpv funcUtils.py $BACKUP
cp -fpv glogTime.py $BACKUP
cp -fpv htmlUtils.py $BACKUP
cp -fpv ops_activate.py $BACKUP
cp -fpv ops_db_insert.py $BACKUP
cp -fpv ops_db_query.py $BACKUP
cp -fpv ops_db_update.py $BACKUP
cp -fpv ops_svr.py $BACKUP
cp -fpv sdb_deta.py $BACKUP
cp -fpv sdb_sqlite.py $BACKUP

# backup production data
echo "================================================"
echo "===> backup production data ..."
cp -fpv $PROD/data/*.csv $BACKUP/data

# push docs
echo "================================================"
echo "===> push docs ..."
cp -fpv README.md $BACKUP
cp -fpv requirements.txt $BACKUP
cp -fpv environment.yaml $BACKUP

# push html
echo "================================================"
echo "===> push html ..."
cp -fpv static/main.css $BACKUP/static
cp -fpv static/mkao2019.jpeg $BACKUP/static
cp -fpv static/ScreenShot_charge.png $BACKUP/static
cp -fpv static/ScreenShot_cookie_manager.png $BACKUP/static
cp -fpv static/ScreenShot_creator.png $BACKUP/static
cp -fpv static/ScreenShot_donate.png $BACKUP/static
cp -fpv static/ScreenShot_login.png $BACKUP/static
cp -fpv static/ScreenShot_resetPW.png $BACKUP/static
cp -fpv static/ScreenShot_settings.png $BACKUP/static
cp -fpv static/ScreenShot_signup.png $BACKUP/static
cp -fpv templates/about.html $BACKUP/templates
cp -fpv templates/layout.html $BACKUP/templates
cp -fpv templates/faq.html $BACKUP/templates

# set file modes
echo "================================================"
echo "===> set file modes ..."
cd $BACKUP
chmod 755 .*
chmod 755 *
chmod 755 data
chmod 644 data/*.csv
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



