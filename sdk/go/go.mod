module github.com/agenthr/agenthr-go

go 1.21

// AgentHR Go SDK - AI-powered resume analysis and candidate ranking system
//
// This SDK provides a Go client for interacting with the AgentHR API.
// It supports all major features including resume parsing, candidate ranking,
// vacancy management, analytics, webhooks, workflows, and plugins.
//
// Quick Start:
//
//	import "github.com/agenthr/agenthr-go"
//
//	client := agenthr.NewClient("your-api-key", nil)
//	vacancies, err := client.Vacancies.List(context.Background(), nil)
//
// For more information, visit https://docs.agenthr.dev
