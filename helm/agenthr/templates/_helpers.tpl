{{/*
Expand the name of the chart.
*/}}
{{- define "agenthr.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "agenthr.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "agenthr.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "agenthr.labels" -}}
helm.sh/chart: {{ include "agenthr.chart" . }}
{{ include "agenthr.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "agenthr.selectorLabels" -}}
app.kubernetes.io/name: {{ include "agenthr.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "agenthr.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "agenthr.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create a default fully qualified postgresql name.
*/}}
{{- define "agenthr.postgresql.fullname" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "%s-postgresql" (include "agenthr.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "postgresql" }}
{{- end }}
{{- end }}

{{/*
Create a default fully qualified redis name.
*/}}
{{- define "agenthr.redis.fullname" -}}
{{- if .Values.redis.enabled }}
{{- printf "%s-redis-master" (include "agenthr.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "redis" }}
{{- end }}
{{- end }}

{{/*
Create the database URL from postgresql values
*/}}
{{- define "agenthr.databaseUrl" -}}
{{- if .Values.secrets.databaseUrl }}
{{- .Values.secrets.databaseUrl }}
{{- else if .Values.postgresql.enabled }}
{{- printf "postgresql://%s:%s@%s:5432/%s" .Values.postgresql.auth.username .Values.postgresql.auth.password (include "agenthr.postgresql.fullname" .) .Values.postgresql.auth.database }}
{{- else }}
{{- printf "postgresql://postgres:postgres@postgresql:5432/resume_analysis" }}
{{- end }}
{{- end }}

{{/*
Create the Redis URL from redis values
*/}}
{{- define "agenthr.redisUrl" -}}
{{- if .Values.secrets.redisUrl }}
{{- .Values.secrets.redisUrl }}
{{- else if .Values.redis.enabled }}
{{- printf "redis://%s:6379/0" (include "agenthr.redis.fullname" .) }}
{{- else }}
{{- printf "redis://redis:6379/0" }}
{{- end }}
{{- end }}
