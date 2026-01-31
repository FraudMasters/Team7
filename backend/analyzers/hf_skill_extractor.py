"""
Hugging Face-based skill extraction from resume text.

This module provides functions to extract relevant skills and keywords
from resume text using pre-trained Hugging Face models, avoiding KeyBERT
and its Keras 3 compatibility issues.
"""
import logging
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Global model instances to avoid reloading on each call
_ner_pipeline = None
_ner_model_name = None
_zero_shot_pipeline = None
_zero_shot_model_name = None

# Model mapping by language
# All models listed here are fine-tuned for NER tasks
LANGUAGE_MODELS = {
    # English models
    "en": "dslim/bert-base-NER",  # English-only, well-tested, fast

    # Russian/multilingual models (fine-tuned for NER)
    # Davlan model supports 10+ languages including Russian and English
    "ru": "Davlan/bert-base-multilingual-cased-ner-hrl",

    # Fallback multilingual model (supports 20+ languages)
    "multilingual": "Davlan/bert-base-multilingual-cased-ner-hrl",
}

# Alternative models with different trade-offs:
# LANGUAGE_MODELS_ALTERNATIVES = {
#     # Russian-specific models (slower but potentially more accurate)
#     "ru_slower": "Babelscape/wikiann-bornholm-ne-2021",  # WikiANN for Russian
#     "ru_deep": "DeepPavlov/rubert-base-cased-conversational",  # Not NER-specific
#
#     # Other multilingual NER models
#     "multilingual_xlm": "xlm-roberta-large-finetuned-conll03-english",  # XLMRoBERTa
#     "multilingual_wikiann": "Babelscape/wikineural-multilingual-ner",  # WikiNEuRal
# }

# Common technical skills for pattern matching
# Structured dictionary with aliases for better matching
SKILLS_TAXONOMY = {
    # Programming Languages
    "programming_languages": {
        "python": ["python", "py", "python3"],
        "java": ["java", "JAVA"],
        "javascript": ["javascript", "js", "ecmascript"],
        "csharp": ["c#", "csharp", "dotnet", ".net"],
        "cpp": ["c++", "c plus plus", "cpp"],
        "c": ["c language", "c programming"],
        "php": ["php", "hypertext preprocessor"],
        "go": ["go", "golang"],
        "ruby": ["ruby"],
        "perl": ["perl"],
        "typescript": ["typescript", "ts"],
        "kotlin": ["kotlin"],
        "swift": ["swift", "swiftui"],
        "rust": ["rust"],
        "scala": ["scala"],
        "r": ["r language", "rstats"],
        "dart": ["dart"],
        "matlab": ["matlab"],
        "groovy": ["groovy"],
        "haskell": ["haskell"],
        "elixir": ["elixir"],
        "erlang": ["erlang"],
        "fsharp": ["f#", "fsharp"],
        "clojure": ["clojure", "cljs"],
        "lua": ["lua"],
        "julia": ["julia"],
        "assembly": ["assembly", "asm", "x86", "arm"],
        "cobol": ["cobol"],
        "fortran": ["fortran"],
        "delphi": ["delphi", "pascal"],
        "abap": ["abap"],
        "plsql": ["pl/sql", "plsql"],
        "tcl": ["tcl", "tk"],
        "bash": ["bash", "sh", "shell script", "shellscript", "posix shell"],
        "powershell": ["powershell", "ps", "pwsh"],
        "vb": ["visual basic", "vb", "vb.net"],
        "objectivec": ["objective-c", "obj-c", "objc"],
        "sql": ["sql", "structured query language", "tsql", "t-sql", "pl/sql"],
    },

    # Web Frontend
    "web_frontend": {
        "html": ["html", "html5", "xhtml"],
        "css": ["css", "css3", "scss", "sass", "less", "stylus"],
        "javascript": ["javascript", "js", "ecmascript", "es6", "es2015", "es2020"],
        "typescript": ["typescript", "ts"],
        "react": ["react", "reactjs", "react.js", "reactjs", "create-react-app", "cra"],
        "next": ["next.js", "nextjs", "next"],
        "nuxt": ["nuxt.js", "nuxtjs", "nuxt"],
        "vue": ["vue.js", "vue", "vuejs", "vue3", "vue 3"],
        "angular": ["angular", "angularjs", "angular 2", "angular2", "angularjs", "ng"],
        "svelte": ["svelte", "sveltekit"],
        "ember": ["ember", "ember.js", "emberjs"],
        "backbone": ["backbone", "backbone.js"],
        "jquery": ["jquery", "jquery-ui", "jquery mobile"],
        "webpack": ["webpack", "webpack 5"],
        "vite": ["vite"],
        "babel": ["babel", "babeljs"],
        "gulp": ["gulp", "gulpjs"],
        "grunt": ["grunt"],
        "parcel": ["parcel"],
        "rollup": ["rollup", "rollup.js"],
        "tailwind": ["tailwind", "tailwindcss", "tailwind css"],
        "bootstrap": ["bootstrap", "twitter bootstrap", "bstp"],
        "material_ui": ["material ui", "mui", "material-ui"],
        "ant_design": ["ant design", "antdesign", "antd"],
        "chakra": ["chakra ui", "chakra"],
        "mui": ["mui", "material-ui"],
        "storybook": ["storybook"],
        "sass": ["sass", "scss"],
        "less": ["less"],
        "styled_components": ["styled-components", "styled components"],
        "emotion": ["emotion"],
        "redux": ["redux", "react-redux", "redux toolkit", "rtk"],
        "mobx": ["mobx"],
        "rxjs": ["rxjs", "reactive extensions"],
        "graphql": ["graphql", "gql", "graphql-js", "apollo", "apollo client", "apollo server"],
        "rest": ["rest", "restful", "rest api", "restful api", "restapis"],
        "fetch": ["fetch api", "fetch"],
        "axios": ["axios"],
        "websocket": ["websocket", "websockets", "socket.io", "socketio"],
        "pwa": ["pwa", "progressive web app", "service worker"],
        "wasm": ["webassembly", "wasm"],
    },

    # Web Backend
    "web_backend": {
        "django": ["django", "django rest framework", "drf"],
        "flask": ["flask"],
        "fastapi": ["fastapi"],
        "spring": ["spring", "spring boot", "spring framework", "springmvc", "spring mvc"],
        "spring_security": ["spring security"],
        "spring_data": ["spring data", "spring data jpa", "spring jdbc"],
        "express": ["express", "express.js", "expressjs", "expressjs"],
        "koa": ["koa", "koa.js"],
        "nestjs": ["nestjs", "nest.js"],
        "laravel": ["laravel"],
        "symfony": ["symfony"],
        "rails": ["ruby on rails", "rails", "ror"],
        "sinatra": ["sinatra"],
        "aspnet": ["asp.net", "aspnet", "asp.net core", "aspnet core", "asp.net mvc", "aspnet mvc"],
        "aspnet_webapi": ["asp.net web api", "asp.net webapi", "webapi"],
        "entity_framework": ["entity framework", "ef", "entityframework", "ef core"],
        "wcf": ["wcf", "windows communication foundation"],
        "fiber": ["fiber", "golang fiber"],
        "buffalo": ["buffalo"],
        "echo": ["echo", "echo framework"],
        "gin": ["gin", "gin framework"],
        "beego": ["beego"],
        "iris": ["iris"],
        "httprouter": ["httprouter"],
        "gorilla": ["gorilla mux", "gorilla"],
        "play": ["play framework", "play", "play scala"],
        "akka": ["akka", "akka http"],
        "vertx": ["vert.x", "vertx"],
        "quarkus": ["quarkus"],
        "micronaut": ["micronaut"],
        "codeigniter": ["codeigniter", "ci"],
        "phalcon": ["phalcon"],
        "cakephp": ["cakephp"],
        "slim": ["slim framework", "slim php"],
        "lumen": ["lumen"],
    },

    # Mobile Development
    "mobile_development": {
        "android": ["android", "android sdk", "android ndk", "kotlin android", "java android"],
        "ios": ["ios", "iphone", "ipad", "cocoa touch", "uikit"],
        "react_native": ["react native", "reactnative", "rn"],
        "flutter": ["flutter", "dart"],
        "xamarin": ["xamarin", "xamarin.forms", "xamarin forms"],
        "ionic": ["ionic", "ionic framework", "ionicframework"],
        "cordova": ["cordova", "apache cordova", "phonegap"],
        "native_script": ["nativescript", "native script"],
        "expo": ["expo"],
        "swiftui": ["swiftui", "swift ui"],
        "jetpack": ["jetpack", "jetpack compose", "android jetpack"],
        "android_studio": ["android studio"],
        "xcode": ["xcode"],
        "gradle": ["gradle"],
        "maven": ["maven"],
    },

    # Desktop Development
    "desktop_development": {
        "electron": ["electron", "electronjs"],
        "tauri": ["tauri"],
        "qt": ["qt", "qt framework", "qt5", "qt6"],
        "gtk": ["gtk", "gtk+", "gtk3", "gtk4"],
        "wxwidgets": ["wxwidgets", "wxpython", "wxwidgets"],
        "win32": ["win32", "winapi", "windows api"],
        "wpf": ["wpf", "windows presentation foundation"],
        "winforms": ["winforms", "windows forms"],
        "maui": ["maui", ".net maui"],
        "avalonia": ["avalonia", "avalonia ui"],
        "uwp": ["uwp", "universal windows platform"],
        "javafx": ["javafx"],
        "swing": ["swing", "java swing"],
        "awt": ["awt", "abstract window toolkit"],
    },

    # Data Science & Machine Learning
    "data_science_ml": {
        "pandas": ["pandas"],
        "numpy": ["numpy"],
        "tensorflow": ["tensorflow", "tf"],
        "pytorch": ["pytorch", "torch"],
        "keras": ["keras"],
        "scikit_learn": ["scikit-learn", "sklearn", "scikit learn"],
        "xgboost": ["xgboost", "xgboost", "xgb"],
        "lightgbm": ["lightgbm", "lgbm"],
        "catboost": ["catboost"],
        "nltk": ["nltk", "natural language toolkit"],
        "spacy": ["spacy", "spacy"],
        "opencv": ["opencv", "cv2"],
        "matplotlib": ["matplotlib"],
        "seaborn": ["seaborn"],
        "plotly": ["plotly"],
        "bokeh": ["bokeh"],
        "jupyter": ["jupyter", "jupyter notebook", "jupyterlab"],
        "spark": ["apache spark", "spark", "pyspark", "sparkml"],
        "hadoop": ["hadoop", "hdfs", "mapreduce"],
        "hive": ["hive", "apache hive"],
        "presto": ["presto", "prestodb", "presto sql"],
        "trino": ["trino"],
        "impala": ["impala"],
        "kafka": ["kafka", "apache kafka"],
        "airflow": ["airflow", "apache airflow"],
        "dbt": ["dbt", "data build tool"],
        "snowflake": ["snowflake"],
        "bigquery": ["bigquery", "gcp bigquery"],
        "redshift": ["redshift", "aws redshift"],
        "databricks": ["databricks"],
        "tableau": ["tableau"],
        "power_bi": ["power bi", "powerbi", "power-bi"],
        "looker": ["looker"],
        "superset": ["superset", "apache superset"],
        "metabase": ["metabase"],
        "grafana": ["grafana"],
        "kibana": ["kibana"],
        "mlflow": ["mlflow"],
        "wandb": ["wandb", "weights and biases"],
        "ray": ["ray", "ray distributed"],
        "dask": ["dask"],
        "polars": ["polars"],
        "vaex": ["vaex"],
        "scrapy": ["scrapy"],
        "beautifulsoup": ["beautifulsoup", "bs4", "beautiful soup"],
        "selenium": ["selenium"],
        "requests": ["requests", "requests python"],
        "urllib": ["urllib", "urllib3"],
    },

    # Deep Learning & AI
    "deep_learning_ai": {
        "tensorflow": ["tensorflow", "tf", "tf2", "tensorflow 2"],
        "keras": ["keras"],
        "pytorch": ["pytorch", "torch"],
        "jax": ["jax", "jax jax"],
        "theano": ["theano"],
        "mxnet": ["mxnet", "apache mxnet"],
        "cntk": ["cntk", "microsoft cognitive toolkit"],
        "caffe": ["caffe", "caffe2"],
        "onnx": ["onnx", "open neural network exchange"],
        "tensorrt": ["tensorrt"],
        "huggingface": ["huggingface", "hugging face", "transformers", "transformers library"],
        "langchain": ["langchain", "lang chain"],
        "llm": ["llm", "large language model", "gpt", "chatgpt", "openai api"],
        "openai": ["openai", "openai api", "gpt-3", "gpt-4", "gpt3", "gpt4"],
        "anthropic": ["anthropic", "claude", "claude ai"],
        "cohere": ["cohere"],
        "pinecone": ["pinecone"],
        "weaviate": ["weaviate"],
        "chromadb": ["chromadb", "chroma db", "chroma"],
        "faiss": ["faiss", "faiss vector similarity"],
        "milvus": ["milvus"],
        "qdrant": ["qdrant"],
        "stable_diffusion": ["stable diffusion", "stability ai"],
        "diffusers": ["diffusers", "huggingface diffusers"],
        "yolo": ["yolo", "you only look once"],
        "vit": ["vision transformer", "vit"],
        "bert": ["bert", "bidirectional encoder representations"],
        "gpt": ["gpt", "generative pre-trained"],
        "resnet": ["resnet", "residual network"],
        "vgg": ["vgg", "visual geometry group"],
        "inception": ["inception", "googlenet", "inceptionv3", "inception v3"],
        "mobilenet": ["mobilenet", "mobile net"],
        "efficientnet": ["efficientnet", "efficient net"],
        "yolov5": ["yolov5", "yolo v5"],
        "yolov8": ["yolov8", "yolo v8"],
    },

    # Databases
    "databases": {
        "postgresql": ["postgresql", "postgres", "postgres", "pg"],
        "mysql": ["mysql", "mysqld"],
        "mariadb": ["mariadb"],
        "sqlite": ["sqlite", "sqlite3"],
        "mssql": ["mssql", "microsoft sql server", "sql server", "azure sql"],
        "oracle": ["oracle", "oracle database", "oracle db", "pl/sql"],
        "mongodb": ["mongodb", "mongo", "mongo atlas", "mongo db"],
        "redis": ["redis", "redis cache", "redisdb"],
        "elasticsearch": ["elasticsearch", "elastic search", "elastic", "es"],
        "cassandra": ["cassandra", "apache cassandra"],
        "dynamodb": ["dynamodb", "amazon dynamodb", "aws dynamodb"],
        "cosmosdb": ["cosmosdb", "azure cosmos db", "cosmos db"],
        "firestore": ["firestore", "cloud firestore"],
        "firebase": ["firebase", "firebase realtime database"],
        "supabase": ["supabase"],
        "neon": ["neon", "neon db"],
        "planet_scale": ["planetscale", "planet scale"],
        "cockroachdb": ["cockroachdb", "cockroach db"],
        "timescaledb": ["timescaledb", "timescale db"],
        "influxdb": ["influxdb", "influx db"],
        "prometheus": ["prometheus", "prometheus db"],
        "grafana": ["grafana", "grafana loki"],
        "clickhouse": ["clickhouse", "click house"],
        "scylladb": ["scylladb", "scylla db"],
        "couchbase": ["couchbase", "couch base"],
        "couchdb": ["couchdb", "couch db"],
        "riak": ["riak"],
        "neo4j": ["neo4j", "neo4j graph database"],
        "arangodb": ["arangodb", "arango db"],
        "orientdb": ["orientdb", "orient db"],
        "faunadb": ["faunadb", "fauna db"],
        "surrealdb": ["surrealdb", "surreal db"],
        "valkey": ["valkey", "keydb", "key db"],
        "dragonflydb": ["dragonflydb", "dragonfly db"],
        "manticore_search": ["manticore", "manticore search"],
        "typesense": ["typesense"],
        "meilisearch": ["meilisearch", "meili search"],
        "algolia": ["algolia"],
        "solr": ["solr", "apache solr"],
        "azure_table": ["azure table storage", "azure table"],
        "azure_blob": ["azure blob storage", "azure blob"],
        "s3": ["s3", "amazon s3", "aws s3"],
        "gcs": ["gcs", "google cloud storage", "google cloud store"],
        "minio": ["minio"],
        "r2": ["r2", "cloudflare r2"],
        "wasabi": ["wasabi", "wasabi storage"],
        "backblaze": ["backblaze", "b2"],
    },

    # DevOps & Cloud
    "devops_cloud": {
        "docker": ["docker", "docker-compose", "docker compose", "dockerfile", "dockerhub"],
        "kubernetes": ["kubernetes", "k8s", "k8s", "kube", "kubectl", "helm", "helm charts"],
        "aws": ["aws", "amazon web services", "amazonwebservices", "ec2", "s3", "lambda", "api gateway", "rds", "dynamodb", "ecs", "eks", "fargate", "cloudfront", "route53", "vpc", "iam", "s3", "cloudwatch", "athena", "glue", "kinesis", "sqs", "sns", "msk", "elasticache", "documentdb", "neptune", "timestream", "opensearch"],
        "azure": ["azure", "microsoft azure", "az", "azure devops", "azure pipelines", "azure functions", "app service", "azure sql", "cosmos db", "blob storage", "key vault", "active directory", "aad", "entra id"],
        "gcp": ["gcp", "google cloud platform", "googlecloud", "gke", "cloud run", "app engine", "appengine", "cloud functions", "bigquery", "pubsub", "dataflow", "dataproc", "cloud storage", "gcs", "iam", "secret manager", "artifact registry"],
        "terraform": ["terraform", "tf", "hcl", "terraform cloud", "terraform enterprise"],
        "ansible": ["ansible", "ansible playbooks", "ansible tower", "awx"],
        "puppet": ["puppet", "puppet enterprise"],
        "chef": ["chef", "chef infra", "chef automate", "inspec"],
        "saltstack": ["saltstack", "salt", "salt cloud"],
        "cfengine": ["cfengine"],
        "rundeck": ["rundeck"],
        "jenkins": ["jenkins", "jenkins ci", "jenkins pipeline"],
        "gitlab_ci": ["gitlab ci", "gitlab-ci", "gitlab cicd", ".gitlab-ci.yml"],
        "github_actions": ["github actions", "github-actions", "gh actions"],
        "circleci": ["circleci", "circle ci"],
        "travis": ["travis ci", "travisci"],
        "bitbucket_pipelines": ["bitbucket pipelines", "bitbucket-pipelines"],
        "drone": ["drone ci", "drone-ci", "drone.io"],
        "concourse": ["concourse", "concourse ci"],
        "spinnaker": ["spinnaker"],
        "argocd": ["argocd", "argo cd", "argo-cd"],
        "flux": ["flux", "flux cd", "fluxcd"],
        "nginx": ["nginx", "enginex", "openresty", "tengine"],
        "apache": ["apache", "apache http server", "httpd"],
        "iis": ["iis", "internet information services", "internet information server"],
        "caddy": ["caddy"],
        "traefik": ["traefik"],
        "envoy": ["envoy", "envoy proxy"],
        "haproxy": ["haproxy", "ha proxy"],
        "prometheus": ["prometheus", "promql"],
        "grafana": ["grafana", "grafana loki", "loki", "tempo"],
        "elk": ["elk", "elasticsearch logstash kibana", "elastic stack"],
        "efk": ["efk", "elasticsearch fluentd kibana"],
        "fluentd": ["fluentd"],
        "fluent_bit": ["fluent bit", "fluentbit"],
        "logstash": ["logstash"],
        "beats": ["beats", "elastic beats", "filebeat", "metricbeat", "packetbeat", "heartbeat", "auditbeat"],
        "kibana": ["kibana"],
        "datadog": ["datadog"],
        "newrelic": ["new relic", "newrelic"],
        "dynatrace": ["dynatrace"],
        "appdynamics": ["appdynamics"],
        "splunk": ["splunk", "splunk enterprise", "splunk cloud"],
        "sumo_logic": ["sumo logic", "sumologic"],
        "loggly": ["loggly"],
        "papertrail": ["papertrail"],
        "logz": ["logz", "logz.io"],
        "sentry": ["sentry"],
        "bugsnag": ["bugsnag"],
        "rollbar": ["rollbar"],
        "airbrake": ["airbrake"],
        "pagerduty": ["pagerduty"],
        "opsgenie": ["opsgenie"],
        "victorops": ["victorops", "victor ops"],
        "pingdom": ["pingdom"],
        "uptimerobot": ["uptimerobot"],
        "statuspage": ["statuspage", "status page"],
        "pagerduty": ["pagerduty"],
        "ssh": ["ssh", "openssh", "secure shell"],
        "ssl_tls": ["ssl", "tls", "openssl"],
        "https": ["https", "http over tls", "http secure"],
        "certificates": ["certificate", "certificates", "x.509", "letsencrypt", "let's encrypt"],
        "oauth": ["oauth", "oauth2", "oauth 2.0", "openid connect", "oidc"],
        "saml": ["saml", "security assertion markup language"],
        "ldap": ["ldap", "active directory", "ad", "openldap"],
        "kerberos": ["kerberos"],
        "jwt": ["jwt", "json web token"],
        "session": ["session", "session management", "cookies"],
        "csrf": ["csrf", "csrf protection", "cross-site request forgery"],
        "xss": ["xss", "cross-site scripting", "xss protection"],
        "sql_injection": ["sql injection", "sql injection prevention", "sqli"],
        "ddos": ["ddos", "distributed denial of service", "ddos protection"],
        "waf": ["waf", "web application firewall"],
        "encryption": ["encryption", "cryptography", "hashing", "aes", "rsa", "sha256"],
        "firewall": ["firewall", "iptables", "nftables", "pf", "windows firewall"],
        "vpn": ["vpn", "virtual private network", "openvpn", "wireguard"],
        "iptable": ["iptables", "nftables"],
    },

    # Version Control & Collaboration
    "version_control": {
        "git": ["git", "gitlab", "github", "bitbucket", "gitKraken", "sourcetree", "gitextensions"],
        "svn": ["svn", "subversion"],
        "mercurial": ["mercurial", "hg"],
        "perforce": ["perforce", "p4"],
        "plastic_scm": ["plastic scm", "plastic"],
        "clearcase": ["clearcase", "ibm rational clearcase"],
        "tfs": ["tfs", "team foundation server", "azure devops server"],
        "vsts": ["vsts", "visual studio team services"],
        "azure_devops": ["azure devops", "azure repos", "azure pipelines"],
        "gitflow": ["gitflow", "github flow", "gitlab flow"],
        "pull_request": ["pull request", "pr", "merge request", "mr"],
        "code_review": ["code review", "peer review", "pr review"],
    },

    # Testing & Quality Assurance
    "testing": {
        "junit": ["junit", "junit5", "junit 5"],
        "testng": ["testng"],
        "pytest": ["pytest", "py.test"],
        "unittest": ["unittest", "pyunit", "python unittest"],
        "nose": ["nose", "nose2"],
        "selenium": ["selenium", "selenium webdriver", "selenium ide", "selenium grid"],
        "cypress": ["cypress", "cypress.io", "cypressio"],
        "playwright": ["playwright", "microsoft playwright"],
        "puppeteer": ["puppeteer"],
        "jest": ["jest", "jest testing"],
        "mocha": ["mocha", "mochajs"],
        "jasmine": ["jasmine"],
        "karma": ["karma", "karma runner", "karma test runner"],
        "chai": ["chai", "chaijs"],
        "supertest": ["supertest"],
        "jmeter": ["jmeter", "apache jmeter"],
        "gatling": ["gatling"],
        "locust": ["locust", "locust.io"],
        "k6": ["k6", "k6 load testing"],
        "artillery": ["artillery"],
        "tsung": ["tsung"],
        "mock": ["mock", "mocking", "mockito", "unittest.mock", "sinon", "sinonjs"],
        "stub": ["stub", "stubbing"],
        "tdd": ["tdd", "test driven development"],
        "bdd": ["bdd", "behavior driven development", "cucumber", "cucumber-js", "behave", "specflow"],
        "code_coverage": ["code coverage", "coverage", "codecov", "coveralls", "istanbul", "nyc"],
        "sonarqube": ["sonarqube", "sonar", "sonarcloud", "sonarlint"],
        "eslint": ["eslint"],
        "prettier": ["prettier", "prettierjs"],
        "black": ["black", "black python formatter"],
        "flake8": ["flake8"],
        "pylint": ["pylint"],
        "mypy": ["mypy"],
        "typescript_eslint": ["typescript-eslint", "@typescript-eslint"],
        "stylelint": ["stylelint"],
        "husky": ["husky", "husky pre-commit"],
        "lint_staged": ["lint-staged", "lint staged"],
    },

    # Build Tools & Package Managers
    "build_tools": {
        "maven": ["maven", "mvn", "pom"],
        "gradle": ["gradle", "gradlew"],
        "ant": ["ant", "apache ant"],
        "sbt": ["sbt", "scala build tool"],
        "leiningen": ["leiningen", "lein"],
        "npm": ["npm", "node package manager"],
        "yarn": ["yarn", "yarnpkg"],
        "pnpm": ["pnpm"],
        "bower": ["bower"],
        "pip": ["pip", "pip3", "pipenv", "poetry", "conda"],
        "virtualenv": ["virtualenv", "venv"],
        "composer": ["composer", "php composer"],
        "nuget": ["nuget", "dotnet restore"],
        "dotnet_cli": ["dotnet cli", "dotnet", "dotnet build", "dotnet publish"],
        "webpack": ["webpack", "webpack 5", "webpackjs"],
        "vite": ["vite"],
        "rollup": ["rollup", "rollup.js", "rollupjs"],
        "parcel": ["parcel", "parcel bundler"],
        "esbuild": ["esbuild", "es build"],
        "babel": ["babel", "babeljs", "babel-loader", "babelrc"],
        "swc": ["swc"],
        "rome": ["rome", "rome tools"],
        "rush": ["rush", "rushjs"],
        "lerna": ["lerna"],
        "nx": ["nx", "nrwl"],
        "turborepo": ["turborepo", "turbo"],
        "make": ["make", "makefile", "cmake", "meson", "ninja"],
        "gcc": ["gcc", "g++", "gnu compiler collection", "clang", "llvm"],
        "rust_cargo": ["cargo", "crates.io", "rust cargo"],
        "go_modules": ["go modules", "gomod", "go.mod", "gopkg"],
    },

    # Project Management & Collaboration
    "project_management": {
        "jira": ["jira", "jira software", "jira align"],
        "confluence": ["confluence"],
        "trello": ["trello"],
        "asana": ["asana"],
        "monday": ["monday.com", "monday com"],
        "notion": ["notion", "notion.so"],
        "linear": ["linear", "linear.app"],
        "clickup": ["clickup"],
        "basecamp": ["basecamp"],
        "slack": ["slack", "slack api"],
        "teams": ["microsoft teams", "ms teams", "teams"],
        "discord": ["discord"],
        "zoom": ["zoom", "zoom api"],
        "skype": ["skype", "skype for business"],
        "figma": ["figma", "figma api"],
        "sketch": ["sketch"],
        "adobe_xd": ["adobe xd", "xd", "experience design"],
        "invision": ["invision", "invisionapp"],
        "mural": ["mural"],
        "miro": ["miro"],
        "miro": ["miro", "miro board"],
        "jamboard": ["jamboard", "google jamboard"],
        "trello": ["trello", "trello api"],
    },

    # Messaging & Queues
    "messaging_queues": {
        "rabbitmq": ["rabbitmq", "rabbit mq", "rabbit"],
        "kafka": ["kafka", "apache kafka", "kafka streaming", "kafka consumer", "kafka producer"],
        "activemq": ["activemq", "active mq", "apache activemq"],
        "ibm_mq": ["ibm mq", "ibm mqseries", "mqseries"],
        "zeromq": ["zeromq", "0mq", "zmq", "zero mq"],
        "nsq": ["nsq"],
        "nats": ["nats", "nats streaming", "jetstream"],
        "redis_streams": ["redis streams", "redis stream"],
        "aws_sqs": ["aws sqs", "sqs", "simple queue service"],
        "aws_sns": ["aws sns", "sns", "simple notification service"],
        "azure_sb": ["azure service bus", "service bus", "asb"],
        "gcp_pubsub": ["gcp pubsub", "google pubsub", "cloud pubsub"],
        "event hubs": ["event hubs", "azure event hubs", "eventhubs"],
        "grpc": ["grpc", "gRPC", "google rpc"],
        "websocket": ["websocket", "websockets", "socket.io", "socketio", "ws", "wss"],
        "sse": ["sse", "server-sent events", "server sent events"],
        "soap": ["soap", "simple object access protocol"],
        "graphql": ["graphql", "gql", "graphql subscriptions", "apollo graphql"],
        "webhook": ["webhook", "webhooks", "web hook"],
    },

    # Operating Systems
    "operating_systems": {
        "linux": ["linux", "gnu/linux", "linux kernel"],
        "ubuntu": ["ubuntu", "ubuntu linux", "canonical ubuntu"],
        "debian": ["debian", "debian gnu/linux"],
        "centos": ["centos", "centos linux", "rhel clone"],
        "rhel": ["red hat", "redhat", "rhel", "red hat enterprise linux"],
        "fedora": ["fedora", "fedora linux"],
        "arch": ["arch linux", "archlinux", "arch"],
        "opensuse": ["opensuse", "suse", "suse linux"],
        "alpine": ["alpine", "alpine linux"],
        "amzn": ["amazon linux", "amzn linux", "aws linux"],
        "windows": ["windows", "microsoft windows", "windows server", "windows 10", "windows 11"],
        "windows_server": ["windows server", "server 2019", "server 2022"],
        "macos": ["macos", "mac os", "mac os x", "osx", "os x"],
        "ios": ["ios", "iphone os", "ipados"],
        "android": ["android", "android os", "google android"],
        "freebsd": ["freebsd", "free bsd"],
        "openbsd": ["openbsd", "open bsd"],
        "netbsd": ["netbsd", "net bsd"],
        "solaris": ["solaris", "sun solaris", "oracle solaris"],
        "aix": ["aix", "ibm aix", "advanced interactive executive"],
        "hpux": ["hp-ux", "hpux", "hp unix"],
        "unix": ["unix", "unix-like", "posix"],
        "shell": ["bash", "sh", "zsh", "fish", "csh", "tcsh", "ksh", "powershell", "pwsh", "cmd"],
        "systemd": ["systemd", "systemd linux"],
        "sysv": ["sysv", "system v", "sysvinit"],
        "upstart": ["upstart"],
        "openrc": ["openrc"],
        "runit": ["runit"],
        "supervisord": ["supervisord", "supervisor"],
    },

    # Methodologies & Practices
    "methodologies": {
        "agile": ["agile", "agile methodology", "agile/scrum"],
        "scrum": ["scrum", "scrum master", "scrum framework", "daily standup", "sprint planning", "sprint retrospective", "sprint review"],
        "kanban": ["kanban", "kanban board", "lean kanban"],
        "lean": ["lean", "lean startup", "lean software development"],
        "xp": ["xp", "extreme programming"],
        "tdd": ["tdd", "test driven development", "test-first"],
        "bdd": ["bdd", "behavior driven development", "behaviour driven"],
        "ddd": ["ddd", "domain driven design"],
        "ci_cd": ["ci/cd", "cicd", "ci cd", "continuous integration", "continuous deployment", "continuous delivery"],
        "devops": ["devops", "devsecops", "devops culture"],
        "gitops": ["gitops", "git ops"],
        "infrastructure_as_code": ["infrastructure as code", "iac"],
        "microservices": ["microservices", "microservice", "micro-service", "micro services"],
        "serverless": ["serverless", "serverless computing", "faas", "function as a service"],
        "soa": ["soa", "service oriented architecture", "service-oriented"],
        "monolith": ["monolith", "monolithic", "monolith architecture"],
        "event_driven": ["event driven", "event-driven architecture", "eda"],
        "cqrs": ["cqrs", "command query responsibility segregation"],
        "event_sourcing": ["event sourcing", "event sourcing pattern"],
        "saga": ["saga", "saga pattern", "saga distributed transaction"],
        "cap": ["cap theorem", "brewer's theorem"],
        "acid": ["acid", "acid transactions"],
        "base": ["base", "basically available soft state eventual consistency"],
        "pacelc": ["pacelc theorem"],
        "oop": ["oop", "object oriented programming", "object-oriented"],
        "functional": ["functional programming", "fp", "pure functional"],
        "solid": ["solid", "solid principles", "single responsibility", "open closed", "liskov substitution", "interface segregation", "dependency inversion"],
        "dry": ["dry", "don't repeat yourself"],
        "kiss": ["kiss", "keep it simple stupid"],
        "yagni": ["yagni", "you ain't gonna need it"],
        "clean_code": ["clean code", "clean architecture", "clean code principles"],
        "design_patterns": ["design patterns", "gang of four", "gof", "singleton", "factory", "observer", "strategy", "builder", "adapter", "decorator", "facade", "proxy", "template method"],
        "refactoring": ["refactoring", "code refactoring", "refactor"],
        "pair_programming": ["pair programming", "pair programming"],
        "mob_programming": ["mob programming", "mob programming"],
        "code_review": ["code review", "pull request review", "pr review", "peer review"],
        "incident_response": ["incident response", "incident management", "postmortem", "post-mortem", "root cause analysis", "rca"],
        "slo": ["slo", "service level objective"],
        "sla": ["sla", "service level agreement"],
        "sli": ["sli", "service level indicator"],
        "sre": ["sre", "site reliability engineering", "site reliability engineer"],
        "chaos_engineering": ["chaos engineering", "chaos testing", "fault injection"],
        "blue_green": ["blue-green", "blue green deployment", "blue-green deployment"],
        "canary": ["canary", "canary deployment", "canary release"],
        "rolling": ["rolling", "rolling deployment", "rolling release"],
        "feature_flag": ["feature flag", "feature toggle", "feature flags"],
    },

    # Security
    "security": {
        "owasp": ["owasp", "owasp top 10", "open web application security project"],
        "security_plus": ["security+", "security plus", "comptia security+"],
        "cissp": ["cissp", "certified information systems security professional"],
        "ceh": ["ceh", "certified ethical hacker"],
        "oscp": ["oscp", "offensive security certified professional"],
        "cisa": ["cisa", "certified information systems auditor"],
        "cism": ["cism", "certified information security manager"],
        "giac": ["giac", "global information assurance certification"],
        "penetration_testing": ["penetration testing", "pen testing", "pentest", "pen test"],
        "vulnerability_assessment": ["vulnerability assessment", "vulnerability scan", "vuln assessment"],
        "bug_bounty": ["bug bounty", "bug bounty program", "hackerone", "bugcrowd"],
        "ctf": ["ctf", "capture the flag", "security ctf"],
        "reverse_engineering": ["reverse engineering", "reversing", "malware analysis"],
        "forensics": ["forensics", "digital forensics", "incident response", "ir"],
        "siem": ["siem", "security information and event management", "splunk siem", "sentinel one"],
        "soc": ["soc", "security operations center", "security operations"],
        "dast": ["dast", "dynamic application security testing", "black box testing"],
        "sast": ["sast", "static application security testing", "white box testing"],
        "ias": ["ias", "interactive application security testing"],
        "dependency_check": ["dependency check", "dependency scanning", "sca", "software composition analysis"],
        "container_security": ["container security", "docker security", "kubernetes security"],
        "cloud_security": ["cloud security", "aws security", "azure security", "gcp security", "cspm", "cloud security posture management"],
        "waf": ["waf", "web application firewall", "cloudflare", "aws waf", "azure waf"],
        "ddos_protection": ["ddos protection", "ddos mitigation", "anti-ddos"],
        "encryption": ["encryption", "cryptography", "aes", "rsa", "ecc", "hash", "sha256", "md5", "pbkdf2", "bcrypt", "scrypt", "argon2"],
        "ssl_tls": ["ssl", "tls", "ssl/tls", "https", "certificate", "pki", "public key infrastructure", "letsencrypt", "certificate authority", "ca"],
        "oauth": ["oauth", "oauth2", "oauth 2.0", "openid connect", "oidc", "saml", "saml2", "ldap", "active directory", "kerberos", "ntlm", "jwt"],
        "authentication": ["authentication", "auth", "authn", "mfa", "multi-factor", "2fa", "two-factor", "sso", "single sign-on", "fido", "fido2", "webauthn", "biometrics"],
        "authorization": ["authorization", "authz", "rbac", "role-based access control", "abac", "attribute-based access control", "acl", "access control list"],
        "session": ["session", "session management", "session hijacking", "session fixation", "cookies", "csrf", "xsrf", "cross-site request forgery"],
        "xss": ["xss", "cross-site scripting", "xss prevention", "content security policy", "csp"],
        "csrf": ["csrf", "cross-site request forgery", "csrf prevention", "xsrf", "sameSite"],
        "sql_injection": ["sql injection", "sqli", "sql injection prevention", "prepared statement", "parameterized query"],
        "xxe": ["xxe", "xml external entity", "xxe attack"],
        "ssrf": ["ssrf", "server-side request forgery", "ssrf attack"],
        "path_traversal": ["path traversal", "directory traversal", "lfi", "local file inclusion", "rfi", "remote file inclusion"],
        "command_injection": ["command injection", "os command injection", "shellshock", "bash bug"],
        "deserialization": ["insecure deserialization", "deserialization attack", "object injection"],
        "clickjacking": ["clickjacking", "ui redress attack", "x-frame-options"],
        "security_headers": ["security headers", "hsts", "strict-transport-security", "x-frame-options", "x-content-type-options", "x-xss-protection", "content-security-policy", "csp", "referrer-policy"],
    },

    # CMS & E-commerce
    "cms_ecommerce": {
        "wordpress": ["wordpress", "wp", "wordpress development", "woocommerce"],
        "drupal": ["drupal", "drupal development", "drupal Commerce"],
        "joomla": ["joomla"],
        "magento": ["magento", "magento 2", "magento2", "adobe commerce"],
        "shopify": ["shopify", "shopify plus", "liquid", "shopify theme"],
        "bigcommerce": ["bigcommerce"],
        "prestashop": ["prestashop"],
        "opencart": ["opencart"],
        "oscommerce": ["oscommerce"],
        "square": ["square", "square online", "square space", "squarespace"],
        "wix": ["wix"],
        "webflow": ["webflow"],
        "squarespace": ["squarespace"],
        "ghost": ["ghost", "ghost cms"],
        "hubspot": ["hubspot", "hubspot cms", "hubspot cos"],
        "contentful": ["contentful"],
        "strapi": ["strapi", "strapi cms", "headless cms"],
        "sanity": ["sanity", "sanity cms"],
        "prismic": ["prismic"],
        "dotdigital": ["dotdigital", "dotmailer"],
        "mailchimp": ["mailchimp", "mailchimp api"],
        "sendgrid": ["sendgrid"],
        "twilio": ["twilio", "twilio api", "twilio sms"],
        "messagebird": ["messagebird"],
        "nexmo": ["nexmo", "vonage"],
    },

    # Game Development
    "game_development": {
        "unity": ["unity", "unity3d", "unity engine", "unity 3d"],
        "unreal": ["unreal", "unreal engine", "unreal engine 4", "unreal engine 5", "ue4", "ue5"],
        "godot": ["godot", "godot engine", "godot 3", "godot 4"],
        "game_maker": ["game maker", "gamemaker", "gml", "yoyo games"],
        "construct": ["construct", "construct 3", "construct 2"],
        "defold": ["defold"],
        "love2d": ["love2d", "löve", "love 2d"],
        "phaser": ["phaser", "phaser js", "phaserjs"],
        "cocos2d": ["cocos2d", "cocos2d-x", "cocos creator"],
        "pixi_js": ["pixi.js", "pixijs", "pixi js"],
        "babylonjs": ["babylon.js", "babylonjs", "babylon js"],
        "three_js": ["three.js", "threejs", "three js", "webgl"],
        "webgl": ["webgl", "webgl2", "web gl"],
        "webgpu": ["webgpu", "web gpu"],
        "spark_ar": ["spark ar", "spark ar studio"],
        "lens_studio": ["lens studio", "snap ar"],
        "unity_asset_store": ["unity asset store", "asset store"],
        "unreal_marketplace": ["unreal marketplace", "ue marketplace"],
        "game_design": ["game design", "level design", "game mechanics", "gameplay"],
        "shader": ["shader", "shaders", "hlsl", "glsl", "shaderlab", "shader graph"],
        "particle": ["particle system", "particles", "vfx", "visual effects", "game vfx"],
        "animation": ["animation", "game animation", "skeletal animation", "blend shapes", "morph targets"],
        "physics": ["physics", "game physics", "physx", "havok", "bullet physics"],
        "networking": ["networking", "multiplayer", "game networking", "photon", "mirror", "unity networking", "unreal networking"],
    },

    # Blockchain & Web3
    "blockchain_web3": {
        "ethereum": ["ethereum", "eth", "solidity", "ether"],
        "bitcoin": ["bitcoin", "btc", "satoshi"],
        "smart_contracts": ["smart contract", "smart contracts", "solidity", "vyper", "chainlink"],
        "web3": ["web3", "web3.js", "web3js", "ethereum dapp", "dapp"],
        "defi": ["defi", "decentralized finance", "dex", "uniswap", "sushiswap", "pancakeswap"],
        "nft": ["nft", "non-fungible token", "opensea", "erc721", "erc1155"],
        "dao": ["dao", "decentralized autonomous organization"],
        "polygon": ["polygon", "matic", "polygon network"],
        "solana": ["solana", "sol", "rust solana"],
        "binance_smart_chain": ["bsc", "binance smart chain", "bnb"],
        "avalanche": ["avalanche", "avax", "avalanche c-chain"],
        "terra": ["terra", "luna", "ust"],
        "cardano": ["cardano", "ada", "haskell"],
        "polkadot": ["polkadot", "dot", "substrate"],
        "cosmos": ["cosmos", "atom", "tendermint"],
        "chainlink": ["chainlink", "link", "oracle"],
        "ipfs": ["ipfs", "interplanetary file system"],
        "filecoin": ["filecoin", "fil"],
        "arweave": ["arweave", "ar"],
        "the_graph": ["the graph", "grt", "graph protocol"],
        "gnosis": ["gnosis", "gnosis chain", "xdai"],
        "optimism": ["optimism", "op", "optimistic ethereum"],
        "arbitrum": ["arbitrum", "arb", "arbitrum one"],
        "metamask": ["metamask", "ethereum wallet", "crypto wallet"],
        "hardhat": ["hardhat", "ethereum development"],
        "truffle": ["truffle", "truffle suite"],
        "foundry": ["foundry", "forge", "cast"],
        "brownie": ["brownie", "python ethereum"],
        "ethers_js": ["ethers.js", "ethersjs"],
        "web3_js": ["web3.js", "web3js"],
        "wagmi": ["wagmi", "rainbowkit", "connectkit"],
        "eip": ["eip", "erc", "ethereum improvement proposal", "erc20", "erc721"],
        "cryptocurrency": ["cryptocurrency", "crypto", "bitcoin", "ethereum", "defi", "nft", "dao", "web3"],
    },

    # IoT & Embedded
    "iot_embedded": {
        "arduino": ["arduino", "arduino ide", "arduino programming"],
        "raspberry_pi": ["raspberry pi", "raspi", "rpi", "raspberry pi programming"],
        "esp32": ["esp32", "esp8266", "esp-idf", "arduino core", "micropython", "circuitpython"],
        "stm32": ["stm32", "stm32cubemx", "hal", "arm cortex-m"],
        "arm": ["arm", "arm cortex", "arm mbed", "keil", "stm32", "nordic", "esp32"],
        "mbed": ["mbed", "arm mbed", "mbed os"],
        "freertos": ["freertos", "free rtos", "rtos"],
        "zephyr": ["zephyr", "zephyr rtos"],
        "riot": ["riot", "riot os"],
        "micropython": ["micropython", "circuitpython", "python embedded"],
        "mqtt": ["mqtt", "mosquitto", "mqtt broker", "iot protocol"],
        "coap": ["coap", "constrained application protocol"],
        "lorawan": ["lorawan", "lora", "long range", "the things network", "ttn"],
        "zigbee": ["zigbee", "zigbee alliance", "iot protocol"],
        "bluetooth": ["bluetooth", "ble", "bluetooth low energy", "bluetooth classic"],
        "wifi": ["wifi", "wi-fi", "esp8266", "esp32", "esp-idf"],
        "nfc": ["nfc", "near field communication", "rfid"],
        "rfid": ["rfid", "radio frequency identification"],
        "pcb": ["pcb", "printed circuit board", "kicad", "eagle", "altium", "easyeda"],
        "fpga": ["fpga", "field programmable gate array", "xilinx", "intel fpga", "verilog", "vhdl"],
        " CPLD": ["cpld", "complex programmable logic device"],
        "hardware": ["hardware", "embedded hardware", "schematic", "electronics", "soldering", "oscilloscope", "multimeter"],
        "firmware": ["firmware", "bootloader", "embedded c", "embedded c++", "bare metal"],
        "rtos": ["rtos", "real time operating system", "freertos", "zephyr", "riot", "threadx"],
    },

    # Reporting & Business Intelligence
    "reporting_bi": {
        "ssrs": ["ssrs", "sql server reporting services", "sql server reporting"],
        "ssis": ["ssis", "sql server integration services", "sql server etl"],
        "ssas": ["ssas", "sql server analysis services", "olap", "business intelligence"],
        "power_bi": ["power bi", "powerbi", "power-bi", "dax", "power query", "m"],
        "tableau": ["tableau", "tableau desktop", "tableau server", "tableau prep"],
        "looker": ["looker", "lookml", "google looker"],
        "qlik": ["qlik", "qlikview", "qlik sense"],
        "spotfire": ["spotfire", "tibco spotfire"],
        "microstrategy": ["microstrategy", "microstrategy bi"],
        "domo": ["domo", "domo bi"],
        "sisense": ["sisense", "periscope data"],
        "thoughtspot": ["thoughtspot", "search-driven analytics"],
        "splunk": ["splunk", "splunk enterprise", "splunk cloud", "splunk siem"],
        "logi": ["logi analytics", "logi report"],
        "crystal_reports": ["crystal reports", "sap crystal reports"],
        "jasper": ["jasper", "jasper reports", "jaspersoft"],
        "pentaho": ["pentaho", "pentaho bi", "kettle", "pentaho data integration"],
        "talend": ["talend", "talend open studio"],
        "informatica": ["informatica", "informatica powercenter"],
        "datastage": ["datastage", "ibm datastage"],
        "ab_initio": ["ab initio", "ab initio etl"],
        "snowflake": ["snowflake", "snowflake data warehouse", "snowflake computing"],
        "databricks": ["databricks", "databricks lakehouse", "spark", "mlflow"],
        "delta_lake": ["delta lake", "databricks delta"],
        "iceberg": ["apache iceberg", "iceberg tables"],
        "hudi": ["apache hudi", "hudi"],
    },

    # Additional Tools & Miscellaneous
    "additional_tools": {
        "postman": ["postman", "postman api"],
        "insomnia": ["insomnia", "insomnia rest"],
        "swagger": ["swagger", "openapi", "openapi specification", "oas", "swagger ui", "swagger editor"],
        "openapi": ["openapi", "openapi specification", "openapi 3.0", "swagger"],
        "graphql": ["graphql", "gql", "apollo graphql", "graphql playground", "graphiql"],
        "protobuf": ["protobuf", "protocol buffers", "proto3", "proto2"],
        "avro": ["avro", "apache avro"],
        "thrift": ["thrift", "apache thrift"],
        "flatbuffers": ["flatbuffers"],
        "msgpack": ["msgpack", "messagepack"],
        "csv": ["csv", "comma separated values"],
        "json": ["json", "javascript object notation"],
        "xml": ["xml", "xpath", "xslt", "xquery", "dtd", "xsd"],
        "yaml": ["yaml", "yml"],
        "toml": ["toml"],
        "ini": ["ini", "config file"],
        "regex": ["regex", "regexp", "regular expression", "re2"],
        "cron": ["cron", "crontab", "scheduler"],
        "logging": ["logging", "log4j", "logback", "slf4j", "python logging", "winston", "pino"],
        "monitoring": ["monitoring", "application monitoring", "apm", "application performance monitoring", "new relic", "datadog", "dynatrace", "appdynamics", "elastic apm"],
        "profiling": ["profiling", "profiler", "performance profiling", "cpu profiler", "memory profiler", "flame graph"],
        "debugging": ["debugging", "debugger", "breakpoint", "gdb", "lldb", "pdb", "chrome devtools", "debug"],
        "testing_manual": ["manual testing", "qa testing", "quality assurance", "software testing"],
        "documentation": ["documentation", "technical writing", "swagger", "openapi", "api documentation", "readme", "wiki", "confluence"],
    },
}


# Flatten the taxonomy for simple pattern matching
# Each key is normalized to lowercase for case-insensitive matching
COMMON_SKILLS = set()
for category, skills in SKILLS_TAXONOMY.items():
    if isinstance(skills, dict):
        for skill_name, aliases in skills.items():
            # Add the base skill name
            COMMON_SKILLS.add(skill_name.lower())
            # Add all aliases
            if isinstance(aliases, list):
                for alias in aliases:
                    # Normalize and add
                    normalized = alias.lower().replace("-", " ").replace("_", " ")
                    COMMON_SKILLS.add(normalized)

# Additional common terms not in categories
ADDITIONAL_SKILLS = {
    # Common tech terms
    "backend", "frontend", "fullstack", "full-stack", "full stack",
    "serverless", "microservices", "microservice", "monolith", "monolithic",
    "api", "rest", "soap", "graphql", "grpc", "webhook",
    "json", "xml", "yaml", "csv", "tsv",
    "ci", "cd", "cicd", "ci/cd", "devops",
    "agile", "scrum", "kanban", "tdd", "bdd",
    "oop", "aop", "functional", "imperative",
    "mvc", "mvvm", "mvp", "clean architecture",
    "solid", "dry", "kiss", "yagni",
    # Programming concepts
    "algorithm", "data structure", "design pattern", "refactoring",
    "unit test", "integration test", "e2e test", "end to end test",
    "code review", "pull request", "merge request",
    "git", "svn", "mercurial", "version control",
    # Web
    "responsive", "pwa", "spa", "single page application",
    "ssr", "server side rendering", "ssg", "static site generation",
    "csr", "client side rendering",
    # Cloud/DevOps
    "iaas", "paas", "saas", "faas",
    "container", "vm", "virtual machine", "bare metal",
    "load balancer", "lb", "cdn", "content delivery network",
    "dns", "ssl", "tls", "https", "http",
    # Databases
    "nosql", "acid", "base", "cap theorem", "transaction",
    # Other
    "unicode", "utf-8", "ascii", "encoding",
    "timezone", "utc", "gmt", "locale", "i18n", "l10n",
    "encoding", "decoding", "serialization", "deserialization",
}

COMMON_SKILLS.update(ADDITIONAL_SKILLS)


def _get_model_for_language(language: str) -> str:
    """
    Get the appropriate NER model name for a given language.

    Args:
        language: Language code ('en', 'ru', 'bg', etc.) or full name

    Returns:
        Hugging Face model name suitable for the language
    """
    # Normalize language code
    lang_lower = (language or "").lower()

    # Map common language codes
    if lang_lower in ["ru", "rus", "russian"]:
        return LANGUAGE_MODELS["ru"]
    elif lang_lower in ["en", "eng", "english"]:
        return LANGUAGE_MODELS["en"]
    else:
        # Default to multilingual for any other language
        return LANGUAGE_MODELS["multilingual"]


def _get_ner_model(model_name: str = None, language: str = None) -> Optional:
    """
    Get or initialize the NER model from Hugging Face.

    Args:
        model_name: Name of the Hugging Face NER model to use.
            If None, will be selected based on language parameter.
        language: Language code ('en', 'ru', etc.) for auto model selection.
            Used only if model_name is None.

    Returns:
        Initialized Hugging Face pipeline or None if loading fails
    """
    global _ner_pipeline, _ner_model_name

    # Auto-select model based on language if not specified
    if model_name is None:
        model_name = _get_model_for_language(language or "en")

    if _ner_pipeline is None or _ner_model_name != model_name:
        try:
            from transformers import pipeline

            logger.info(f"Loading NER model: {model_name}")
            _ner_pipeline = pipeline(
                "ner",
                model=model_name,
                aggregation_strategy="simple",  # Merge sub-tokens
                device=-1,  # Use CPU (change to 0 for GPU)
            )
            _ner_model_name = model_name
            logger.info(f"NER model '{model_name}' loaded successfully")
        except ImportError as e:
            logger.error(f"Transformers not installed: {e}")
            logger.error("Install with: pip install transformers torch")
            _ner_pipeline = None
        except Exception as e:
            logger.error(f"Failed to load NER model '{model_name}': {e}")
            _ner_pipeline = None

    return _ner_pipeline


def _get_zero_shot_model(model_name: str = "facebook/bart-large-mnli") -> Optional:
    """
    Get or initialize the zero-shot classification model.

    Args:
        model_name: Name of the Hugging Face model for zero-shot classification

    Returns:
        Initialized Hugging Face pipeline or None if loading fails
    """
    global _zero_shot_pipeline

    if _zero_shot_pipeline is None:
        try:
            from transformers import pipeline

            logger.info(f"Loading zero-shot model: {model_name}")
            _zero_shot_pipeline = pipeline("zero-shot-classification", model=model_name)
            logger.info("Zero-shot model loaded successfully")
        except ImportError as e:
            logger.error(f"Transformers not installed: {e}")
            _zero_shot_pipeline = None
        except Exception as e:
            logger.error(f"Failed to load zero-shot model: {e}")
            _zero_shot_pipeline = None

    return _zero_shot_pipeline


def extract_skills_ner(
    text: str,
    *,
    top_n: int = 10,
    model_name: str = None,
    language: str = None,
    min_score: float = 0.5,
    skill_entity_types: Optional[List[str]] = None,
) -> Dict[str, Optional[Union[List[str], List[Tuple[str, float]], str]]]:
    """
    Extract skills from resume text using NER (Named Entity Recognition).

    This function uses a pre-trained NER model to identify entities in the text
    that likely represent skills, technologies, tools, or certifications.

    Args:
        text: Input text to extract skills from
        top_n: Maximum number of skills to return
        model_name: Hugging Face model name for NER (None for auto-selection based on language)
        language: Language code ('en', 'ru', etc.) for automatic model selection
        min_score: Minimum confidence score threshold (0.0 to 1.0)
        skill_entity_types: Entity types to consider as skills.
            Defaults to ['ORG', 'PRODUCT', 'SKILL'] for generic models.
            For resume-specific models, use ['SKILL'].

    Returns:
        Dictionary containing:
            - skills: List of extracted skills (without scores)
            - skills_with_scores: List of (skill, score) tuples
            - count: Number of skills extracted
            - model: Model name used
            - error: Error message if extraction failed

    Examples:
        >>> text = "John Doe is a Python developer with experience in Django..."
        >>> result = extract_skills_ner(text, top_n=5)
        >>> print(result["skills"])
        ['Python', 'Django', 'developer']
    """
    # Default entity types that often indicate skills
    if skill_entity_types is None:
        skill_entity_types = ['ORG', 'PRODUCT', 'SKILL']

    # Validate input
    if not text or not isinstance(text, str):
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "Text must be a non-empty string",
        }

    text = text.strip()
    if len(text) < 10:
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "Text too short for skill extraction (min 10 chars)",
        }

    try:
        # Get or initialize model (language-aware selection)
        ner_model = _get_ner_model(model_name, language=language)

        # Track actual model used for return value
        actual_model = model_name or _get_model_for_language(language or "en")

        if ner_model is None:
            return {
                "skills": None,
                "skills_with_scores": None,
                "count": 0,
                "model": model_name,
                "error": "Failed to load NER model. Install: pip install transformers torch",
            }

        # Truncate text if too long (BERT max is 512 tokens)
        max_length = 5000  # Character limit (was 1000, increased for better resume coverage)
        if len(text) > max_length:
            text = text[:max_length]
            logger.warning(f"Text truncated to {max_length} characters for NER")

        # Extract entities
        logger.info(f"Extracting skills using NER from text (length={len(text)})")
        entities = ner_model(text)

        # Filter entities by type and score
        skills_with_scores = []
        for entity in entities:
            entity_text = entity.get('word', '')
            entity_group = entity.get('entity_group', entity.get('entity', ''))
            score = entity.get('score', 0.0)

            # Check if this entity type should be considered a skill
            entity_type_upper = entity_group.upper()
            is_skill_type = any(
                skill_type.upper() in entity_type_upper
                for skill_type in skill_entity_types
            )

            if is_skill_type and score >= min_score:
                # Additional filtering: skills should have some technical characteristics
                if _is_likely_skill(entity_text):
                    skills_with_scores.append((entity_text, score))

        # Remove duplicates while preserving highest scores
        seen = {}
        for skill, score in skills_with_scores:
            skill_lower = skill.lower()
            if skill_lower not in seen or score > seen[skill_lower][1]:
                seen[skill_lower] = (skill, score)

        skills_with_scores = sorted(seen.values(), key=lambda x: x[1], reverse=True)

        # Limit to top_n
        skills_with_scores = skills_with_scores[:top_n]
        skills = [skill for skill, _ in skills_with_scores]

        logger.info(f"Extracted {len(skills)} skills using NER")

        return {
            "skills": skills if skills else None,
            "skills_with_scores": skills_with_scores if skills_with_scores else None,
            "count": len(skills),
            "model": actual_model,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Failed to extract skills with NER: {e}")
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": actual_model if 'actual_model' in locals() else model_name,
            "error": f"NER extraction failed: {str(e)}",
        }


def _is_likely_skill(text: str) -> bool:
    """
    Heuristic to determine if a text fragment is likely a technical skill.

    Args:
        text: Text to evaluate

    Returns:
        True if text has characteristics of a technical skill
    """
    if not text or len(text) < 2:
        return False

    text_lower = text.lower().strip()
    text_stripped = text.strip()

    # Filter out common non-skill patterns from resumes
    _non_skill_patterns = [
        # Resume headers/titles
        'developer at', 'engineer at', 'manager at', 'analyst at',
        'work experience', 'education', 'skills', 'experience',
        'years of experience', 'year of experience',
        'recommendations are available', 'references available',
        'available upon request', 'upon request',
        # Resume sections
        'summary', 'profile', 'objective', 'career', 'professional',
        # Job title fragments
        'with ', 'years of', 'year of', 'month', 'months',
        # Locations
        'israel', 'tel aviv', 'new york', 'san francisco', 'rehovot',
        # Company/organization fragments
        'ltd', 'inc', 'llc', 'corp', ' ltd', ' inc',
        # Verbs/actions - full word match only
        'developed ', 'managed ', 'created ', 'designed ', 'implemented ',
        # Common phrases
        'contact:', 'email:', 'phone:', 'linkedIn:', 'linkedin:',
        # Design phrases
        'graphic & 3d design', '3d design (', 'design (',
        # Non-technical text
        'birthday:', 'residence:', 'languages:',
    ]

    # Check if any non-skill pattern matches
    for pattern in _non_skill_patterns:
        if pattern in text_lower:
            return False

    # Filter out text with problematic prefixes/suffixes
    _problematic_prefixes = [
        'programming languages:', 'languages:', 'web:', 'ide/tools:',
        'technologies:', 'databases:', 'os:', 'additional skills:',
    ]
    for prefix in _problematic_prefixes:
        if text_lower.startswith(prefix):
            # Extract actual skill after prefix
            actual_skill = text_lower[len(prefix):].strip()
            if ':' in actual_skill or len(actual_skill) < 2:
                return False

    # Filter out text ending with unmatched parentheses
    if (text_stripped.endswith(')') and not text_stripped.startswith('(')) or \
       (text_stripped.endswith('(') and not text_stripped.endswith(')')):
        # Exception for known valid skills with parentheses
        valid_paren_skills = ['node.js', 'vue.js', 'next.js', 'react.js', 'angular.js',
                               'c++', 'c#', 'c sharp', 'f#', 'f sharp', '.net']
        if not any(v in text_lower for v in valid_paren_skills):
            return False

    # Filter out fragments with unmatched parentheses anywhere
    if text.count('(') != text.count(')'):
        # Exception for known valid skills with parentheses
        valid_paren_skills = ['node.js', 'vue.js', 'next.js', 'react.js', 'angular.js',
                               'c++', 'c#', 'c sharp', 'f#', 'f sharp']
        if not any(v in text_lower for v in valid_paren_skills):
            return False

    # Filter out overly long "skills" (likely sentences)
    if len(text_stripped.split()) > 5:
        return False

    # Filter out all-caps headers and titles (with minor exceptions)
    if text_stripped.isupper() and len(text_stripped.split()) > 1:
        # Allow common all-caps skills
        all_caps_exceptions = {'sql', 'api', 'ai', 'ml', 'ui', 'ux', 'css', 'html',
                               'ios', 'os', 'ai/ml', 'crm', 'erp', 'saas', 'paas', 'iaas'}
        if text_lower not in all_caps_exceptions:
            return False

    # Filter out sentences starting with lowercase (continuation fragments)
    if text_stripped and text_stripped[0].islower():
        return False

    # Filter out text that looks like a sentence (has common sentence starters)
    _sentence_starters = ['the', 'a ', 'an ', 'this', 'that', 'these', 'those',
                           'my', 'his', 'her', 'our', 'their', 'i ', 'we ', 'they ']
    for starter in _sentence_starters:
        if text_lower.startswith(starter):
            return False

    # Filter out specific problematic patterns
    _blacklisted = [
        'developer at', 'engineer at', 'manager at', 'analyst at',
        'ltd', 'inc', 'llc', 'corp',
        'recommendations are', 'references available',
    ]
    for blacklisted in _blacklisted:
        if blacklisted in text_lower:
            return False

    # Skills often have these characteristics
    has_uppercase = any(c.isupper() for c in text)
    has_digit = any(c.isdigit() for c in text)
    has_special_char = any(c in '.+-/#@' for c in text)
    is_multiword = ' ' in text

    # At least one characteristic should be present for short skills
    if len(text) <= 10 and not (has_uppercase or has_digit or has_special_char):
        # Common short skills exception
        short_skills = {'c', 'r', 'go', 'rust', 'dart', 'java', 'ruby', 'perl',
                       'php', 'html', 'css', 'sql', 'sass', 'less', 'git', 'svn'}
        if text_lower not in short_skills:
            return False

    return True


def extract_skills_pattern_matching(
    text: str,
    skill_list: Optional[set] = None,
    *,
    top_n: int = 20,
    case_sensitive: bool = False,
) -> Dict[str, Optional[Union[List[str], List[Tuple[str, float]], str]]]:
    """
    Extract skills from resume text using pattern matching.

    This function searches for known technical skills in the text using
    pattern matching. It's fast and works well for both English and Russian text.

    Args:
        text: Input text to extract skills from
        skill_list: Set of skills to search for (defaults to COMMON_SKILLS)
        top_n: Maximum number of skills to return
        case_sensitive: Whether to do case-sensitive matching

    Returns:
        Dictionary containing:
            - skills: List of extracted skills (without scores)
            - skills_with_scores: List of (skill, count) tuples (count = occurrences)
            - count: Number of skills extracted
            - model: "pattern-matching"
            - error: Error message if extraction failed
    """
    import re

    if skill_list is None:
        skill_list = COMMON_SKILLS

    # Validate input
    if not text or not isinstance(text, str):
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": "pattern-matching",
            "error": "Text must be a non-empty string",
        }

    text = text.strip()
    if len(text) < 10:
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": "pattern-matching",
            "error": "Text too short for skill extraction (min 10 chars)",
        }

    try:
        # Prepare text for matching
        search_text = text if case_sensitive else text.lower()

        # Find skills with their counts
        skills_found = {}
        for skill in skill_list:
            skill_pattern = skill if case_sensitive else skill.lower()
            # Count occurrences (using word boundaries to avoid partial matches)
            pattern = r'\b' + re.escape(skill_pattern) + r'\b'
            matches = re.findall(pattern, search_text)
            if matches:
                # Preserve original casing from skill list
                skills_found[skill] = len(matches)

        # Convert to (skill, score) tuples where score = count
        skills_with_scores = [
            (skill, count) for skill, count in skills_found.items()
        ]

        # Sort by count (descending) and limit to top_n
        skills_with_scores = sorted(skills_with_scores, key=lambda x: x[1], reverse=True)[:top_n]
        skills = [skill for skill, _ in skills_with_scores]

        logger.info(f"Extracted {len(skills)} skills using pattern matching")

        return {
            "skills": skills if skills else None,
            "skills_with_scores": skills_with_scores if skills_with_scores else None,
            "count": len(skills),
            "model": "pattern-matching",
            "error": None,
        }

    except Exception as e:
        logger.error(f"Pattern matching extraction failed: {e}")
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": "pattern-matching",
            "error": f"Pattern matching failed: {str(e)}",
        }


def extract_skills_zero_shot(
    text: str,
    candidate_skills: List[str],
    *,
    top_n: int = 10,
    model_name: str = "facebook/bart-large-mnli",
    min_score: float = 0.3,
    multi_label: bool = True,
) -> Dict[str, Optional[Union[List[str], List[Tuple[str, float]], str]]]:
    """
    Extract skills from resume text using zero-shot classification.

    This function uses zero-shot classification to determine which skills from
    a provided list are present in the resume text. This is useful when you have
    a predefined taxonomy of skills.

    Args:
        text: Input text (resume or job description)
        candidate_skills: List of potential skills to search for
        top_n: Maximum number of skills to return
        model_name: Hugging Face model name for zero-shot classification
        min_score: Minimum confidence score threshold (0.0 to 1.0)
        multi_label: Whether to allow multiple labels (True for skills)

    Returns:
        Dictionary containing:
            - skills: List of extracted skills (without scores)
            - skills_with_scores: List of (skill, score) tuples
            - count: Number of skills extracted
            - model: Model name used
            - error: Error message if extraction failed

    Examples:
        >>> text = "Experienced Python developer with Django and PostgreSQL knowledge"
        >>> candidates = ["Python", "Java", "Django", "React", "PostgreSQL", "MongoDB"]
        >>> result = extract_skills_zero_shot(text, candidates, top_n=3)
        >>> print(result["skills"])
        ['Python', 'Django', 'PostgreSQL']
    """
    # Validate input
    if not text or not isinstance(text, str):
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "Text must be a non-empty string",
        }

    if not candidate_skills or not isinstance(candidate_skills, list):
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "candidate_skills must be a non-empty list",
        }

    text = text.strip()
    if len(text) < 10:
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "Text too short for skill extraction (min 10 chars)",
        }

    try:
        # Get or initialize model
        zero_shot_model = _get_zero_shot_model(model_name)

        if zero_shot_model is None:
            return {
                "skills": None,
                "skills_with_scores": None,
                "count": 0,
                "model": model_name,
                "error": "Failed to load zero-shot model. Install: pip install transformers torch",
            }

        # Truncate text if too long
        max_length = 5000  # Character limit for zero-shot (increased from 2000)
        if len(text) > max_length:
            text = text[:max_length]
            logger.warning(f"Text truncated to {max_length} characters for zero-shot")

        # Run zero-shot classification
        logger.info(
            f"Running zero-shot classification with {len(candidate_skills)} candidate skills"
        )
        results = zero_shot_model(
            text,
            candidate_skills,
            multi_label=multi_label,
        )

        # Pair labels with scores and filter by threshold
        skills_with_scores = [
            (label, score)
            for label, score in zip(results["labels"], results["scores"])
            if score >= min_score
        ]

        # Sort by score (descending) and limit to top_n
        skills_with_scores = sorted(skills_with_scores, key=lambda x: x[1], reverse=True)[
            :top_n
        ]
        skills = [skill for skill, _ in skills_with_scores]

        logger.info(f"Extracted {len(skills)} skills using zero-shot classification")

        return {
            "skills": skills if skills else None,
            "skills_with_scores": skills_with_scores if skills_with_scores else None,
            "count": len(skills),
            "model": model_name,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Failed to extract skills with zero-shot: {e}")
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": f"Zero-shot extraction failed: {str(e)}",
        }


def extract_resume_skills(
    resume_text: str,
    *,
    method: str = "ner",
    candidate_skills: Optional[List[str]] = None,
    top_n: int = 10,
    **kwargs,
) -> Dict[str, Optional[Union[List[str], List[Tuple[str, float]], str]]]:
    """
    Extract skills from resume text using the specified method.

    This is a convenience function that automatically selects the appropriate
    extraction method based on the parameters provided.

    Args:
        resume_text: Resume text to extract skills from
        method: Extraction method to use:
            - 'ner': Use NER model (doesn't require candidate skills)
            - 'pattern': Use pattern matching with COMMON_SKILLS (fast, works for any language)
            - 'zero-shot': Use zero-shot classification (requires candidate_skills)
            - 'hybrid': Try pattern matching, then NER, then zero-shot as fallbacks
        candidate_skills: List of candidate skills (required for zero-shot)
        top_n: Maximum number of skills to return
        **kwargs: Additional parameters passed to the extraction function

    Returns:
        Dictionary containing extracted skills and metadata

    Examples:
        >>> # Using NER (no candidate skills needed)
        >>> result = extract_resume_skills(resume_text, method='ner', top_n=10)

        >>> # Using pattern matching (fast, works for any language)
        >>> result = extract_resume_skills(resume_text, method='pattern', top_n=20)

        >>> # Using zero-shot with predefined skill taxonomy
        >>> skills_taxonomy = ["Python", "Java", "JavaScript", "Django", "React"]
        >>> result = extract_resume_skills(
        ...     resume_text,
        ...     method='zero-shot',
        ...     candidate_skills=skills_taxonomy,
        ...     top_n=5
        ... )

        >>> # Hybrid: try pattern, then NER, then zero-shot
        >>> result = extract_resume_skills(
        ...     resume_text,
        ...     method='hybrid',
        ...     candidate_skills=skills_taxonomy,
        ...     top_n=10
        ... )
    """
    if method == "pattern":
        return extract_skills_pattern_matching(resume_text, top_n=top_n, **kwargs)

    elif method == "ner":
        return extract_skills_ner(resume_text, top_n=top_n, **kwargs)

    elif method == "zero-shot":
        if not candidate_skills:
            return {
                "skills": None,
                "skills_with_scores": None,
                "count": 0,
                "model": "zero-shot",
                "error": "candidate_skills is required for zero-shot method",
            }
        return extract_skills_zero_shot(
            resume_text, candidate_skills, top_n=top_n, **kwargs
        )

    elif method == "hybrid":
        # Try pattern matching first (fast, language-agnostic)
        # Filter out language parameter as pattern matching doesn't need it
        pattern_kwargs = {k: v for k, v in kwargs.items() if k != 'language'}
        pattern_result = extract_skills_pattern_matching(resume_text, top_n=top_n, **pattern_kwargs)

        # If pattern found good results, return them
        if pattern_result.get("count", 0) >= 5:
            return pattern_result

        # Try NER as second option
        ner_result = extract_skills_ner(resume_text, top_n=top_n, **kwargs)

        # Combine pattern and NER results, removing duplicates
        pattern_skills = set(pattern_result.get("skills") or [])
        ner_skills = set(ner_result.get("skills") or [])

        combined_skills = list(pattern_skills | ner_skills)
        if combined_skills:
            # Create combined results
            combined_with_scores = []
            for skill in combined_skills:
                # Use counts from pattern or score from NER
                pattern_scores = {s: sc for s, sc in (pattern_result.get("skills_with_scores") or [])}
                ner_scores = {s: sc for s, sc in (ner_result.get("skills_with_scores") or [])}

                if skill in pattern_scores:
                    combined_with_scores.append((skill, pattern_scores[skill]))
                elif skill in ner_scores:
                    combined_with_scores.append((skill, ner_scores[skill]))

            combined_with_scores = sorted(combined_with_scores, key=lambda x: x[1], reverse=True)[:top_n]
            return {
                "skills": [s for s, _ in combined_with_scores],
                "skills_with_scores": combined_with_scores,
                "count": len(combined_with_scores),
                "model": f"hybrid (pattern + {ner_result.get('model', 'ner')})",
                "error": None,
            }

        # If both failed and we have candidate_skills, try zero-shot
        if ner_result.get("error") and candidate_skills:
            logger.info("Pattern and NER failed, trying zero-shot classification")
            return extract_skills_zero_shot(
                resume_text, candidate_skills, top_n=top_n, **kwargs
            )

        return ner_result

    else:
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": "none",
            "error": f"Unknown method: {method}. Use 'pattern', 'ner', 'zero-shot', or 'hybrid'",
        }


def extract_top_skills(
    text: str,
    top_n: int = 10,
    method: str = "ner",
    language: str = "english",
) -> Dict[str, Optional[Union[List[str], List[Tuple[str, float]], str]]]:
    """
    Extract top skills from resume text (convenience function).

    This function provides a simple interface optimized for skill extraction
    from resumes. It uses NER by default, which doesn't require a predefined
    skill list.

    Args:
        text: Resume text to extract skills from
        top_n: Number of top skills to return (default: 10)
        method: Extraction method ('ner' or 'zero-shot')
        language: Document language ('english' or 'russian')
            Note: Currently only affects logging, model selection is automatic

    Returns:
        Dictionary containing:
            - skills: List of extracted skills (without scores)
            - skills_with_scores: List of (skill, score) tuples
            - count: Number of skills extracted
            - error: Error message if extraction failed

    Examples:
        >>> text = "Skills: Python, Django, PostgreSQL, Machine Learning..."
        >>> result = extract_top_skills(text, top_n=5)
        >>> print(result["skills"])
        ['Python', 'Django', 'PostgreSQL', 'Machine Learning']
    """
    logger.info(f"Extracting top {top_n} skills using {method} method (language={language})")

    result = extract_resume_skills(
        text,
        method=method,
        top_n=top_n,
        language=language,
    )

    return {
        "skills": result.get("skills"),
        "skills_with_scores": result.get("skills_with_scores"),
        "count": result.get("count", 0),
        "error": result.get("error"),
    }


def extract_resume_keywords(
    resume_text: str,
    language: str = "english",
    include_keyphrases: bool = True,
    method: str = "ner",
) -> Dict[str, Optional[Union[List[str], Dict[str, List[Tuple[str, float]]], str]]]:
    """
    Extract keywords optimized for resume analysis.

    This function provides a drop-in replacement for the KeyBERT-based
    extract_resume_keywords function, using Hugging Face models instead.

    Args:
        resume_text: Full resume text
        language: Document language ('english' or 'russian')
        include_keyphrases: Whether to include multi-word phrases (ignored for NER)
        method: Extraction method to use

    Returns:
        Dictionary containing:
            - single_words: List of single-word keywords with scores
            - keyphrases: List of multi-word phrases with scores
            - all_keywords: Combined list of all extracted keywords
            - error: Error message if extraction failed

    Examples:
        >>> result = extract_resume_keywords(resume_text, language="english")
        >>> print(result["all_keywords"])
        ['Python', 'Machine Learning', 'Django', 'REST API']
    """
    try:
        result = extract_resume_skills(
            resume_text,
            method=method,
            top_n=20,  # Get more to separate single words from phrases
            language=language,
        )

        if result.get("error"):
            return {
                "single_words": None,
                "keyphrases": None,
                "all_keywords": None,
                "error": result["error"],
            }

        skills_with_scores = result.get("skills_with_scores") or []

        # Separate single words from phrases
        single_words = [(s, score) for s, score in skills_with_scores if " " not in s]
        keyphrases = [(s, score) for s, score in skills_with_scores if " " in s]

        # Combine and deduplicate
        all_keywords = [s for s, _ in single_words] + [s for s, _ in keyphrases]

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in all_keywords:
            if kw.lower() not in seen:
                seen.add(kw.lower())
                unique_keywords.append(kw)

        return {
            "single_words": single_words[:15],  # Limit results
            "keyphrases": keyphrases[:10],
            "all_keywords": unique_keywords,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Resume keyword extraction failed: {e}")
        return {
            "single_words": None,
            "keyphrases": None,
            "all_keywords": None,
            "error": f"Extraction failed: {str(e)}",
        }
