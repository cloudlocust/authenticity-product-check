docker compose -f dev_scripts/docker/docker-compose.yml up authenticity-product-db -d -db
docker compose -f dev_scripts/docker/docker-compose.yml up -d pgadmin4
echo "DB_HOST="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'  authenticity-product-db ) > dev_scripts/.local.env
