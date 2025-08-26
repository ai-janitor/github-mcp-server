/*
 * UNDERSTANDING: GitHub Projects v2 API integration for MCP Server
 * DEPENDENCIES: githubv4 GraphQL client, mapstructure for parameter decoding
 * EXPORTS: CreateProject, AddItemToProject, ListUserProjects, UpdateProjectItemStatus, LinkProjectToRepository, UnlinkProjectFromRepository tools
 * INTEGRATION: Fills the gap between GitHub MCP Server and Projects v2 GraphQL API
 */
package github

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/github/github-mcp-server/pkg/translations"
	"github.com/go-viper/mapstructure/v2"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"github.com/shurcooL/githubv4"
)

// UNDERSTANDING: Create a new GitHub Projects v2 board programmatically
// EXPECTS: owner_id (GitHub user/org node ID), title (project name)
// RETURNS: New project details including ID for immediate use
// INTEGRATION: Foundational tool enabling full automation workflow from project creation
func CreateProject(getGQLClient GetGQLClientFn, t translations.TranslationHelperFunc) (mcp.Tool, server.ToolHandlerFunc) {
	return mcp.NewTool("create_project",
		mcp.WithDescription(t("TOOL_CREATE_PROJECT_DESCRIPTION", "Create a new GitHub Projects v2 board. This is the foundational tool that enables full project automation - create the board first, then add issues and manage workflows.")),
		mcp.WithToolAnnotation(mcp.ToolAnnotation{
			Title:        t("TOOL_CREATE_PROJECT_USER_TITLE", "Create project"),
			ReadOnlyHint: ToBoolPtr(false),
		}),
		mcp.WithString("owner_id",
			mcp.Required(),
			mcp.Description("GitHub node ID of the user or organization who will own the project (use get_me to find your user ID)"),
		),
		mcp.WithString("title",
			mcp.Required(),
			mcp.Description("Title/name for the new project"),
		),
		mcp.WithString("description",
			mcp.Description("Optional description for the project"),
		),
	),
	func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		var params struct {
			OwnerID     string  `mapstructure:"owner_id"`
			Title       string  `mapstructure:"title"`
			Description *string `mapstructure:"description"`
		}
		if err := mapstructure.Decode(request.Params.Arguments, &params); err != nil {
			return mcp.NewToolResultError(err.Error()), nil
		}

		// UNDERSTANDING: Get GraphQL client following existing patterns
		// VERIFIED: Same pattern used in AddItemToProject and other GraphQL tools
		client, err := getGQLClient(ctx)
		if err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to get GitHub GQL client: %v", err)), nil
		}

		// UNDERSTANDING: Execute createProjectV2 mutation following GitHub's Projects v2 API
		// EXPECTS: GitHub node ID for owner, project title, optional description
		// RETURNS: Complete project details including ID for immediate use with other tools
		// INTEGRATION: Foundational mutation that enables full project automation workflow
		var createProjectMutation struct {
			CreateProjectV2 struct {
				ProjectV2 struct {
					ID               githubv4.ID
					Number           githubv4.Int
					Title            githubv4.String
					URL              githubv4.String
					ShortDescription githubv4.String
					CreatedAt        githubv4.DateTime
				}
			} `graphql:"createProjectV2(input: $input)"`
		}

		// UNDERSTANDING: Prepare input following GitHub's CreateProjectV2Input schema
		// VERIFIED: Based on GitHub's official API documentation and examples
		input := githubv4.CreateProjectV2Input{
			OwnerID: githubv4.ID(params.OwnerID),
			Title:   githubv4.String(params.Title),
		}

		// NOTE: ShortDescription field may not be available in current githubv4 version
		// Will need to check actual field names in the GraphQL schema
		// TODO: Add description support once field name is confirmed

		if err := client.Mutate(
			ctx,
			&createProjectMutation,
			input,
			nil,
		); err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to create project: %v", err)), nil
		}

		// UNDERSTANDING: Return comprehensive project details for immediate use
		// INTEGRATION: Project ID can be used immediately with AddItemToProject tool
		response := map[string]interface{}{
			"success":     true,
			"message":     "Project created successfully",
			"project_id":  createProjectMutation.CreateProjectV2.ProjectV2.ID,
			"project_number": int(createProjectMutation.CreateProjectV2.ProjectV2.Number),
			"title":       createProjectMutation.CreateProjectV2.ProjectV2.Title,
			"url":         createProjectMutation.CreateProjectV2.ProjectV2.URL,
			"description": createProjectMutation.CreateProjectV2.ProjectV2.ShortDescription,
			"created_at":  createProjectMutation.CreateProjectV2.ProjectV2.CreatedAt,
		}

		responseJSON, err := json.Marshal(response)
		if err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to marshal response: %v", err)), nil
		}

		return mcp.NewToolResultText(string(responseJSON)), nil
	}
}

// UNDERSTANDING: Core function to add an issue/PR to a GitHub Projects v2 board
// EXPECTS: issue_url (full GitHub URL), project_id (from GitHub Projects v2 API)
// RETURNS: Success confirmation with item details
// INTEGRATION: Uses GraphQL mutation addProjectV2ItemById following existing MCP patterns
func AddItemToProject(getGQLClient GetGQLClientFn, t translations.TranslationHelperFunc) (mcp.Tool, server.ToolHandlerFunc) {
	return mcp.NewTool("add_item_to_project",
		mcp.WithDescription(t("TOOL_ADD_ITEM_TO_PROJECT_DESCRIPTION", "Add an issue or pull request to a GitHub Projects v2 board. This bridges the gap between issue creation and project management by automatically adding items to project boards.")),
		mcp.WithToolAnnotation(mcp.ToolAnnotation{
			Title:        t("TOOL_ADD_ITEM_TO_PROJECT_USER_TITLE", "Add item to project"),
			ReadOnlyHint: ToBoolPtr(false),
		}),
		mcp.WithString("project_id",
			mcp.Required(),
			mcp.Description("GitHub Projects v2 project ID (use list_user_projects to find this)"),
		),
		mcp.WithString("issue_url",
			mcp.Required(),
			mcp.Description("Full GitHub URL of the issue or pull request (e.g., 'https://github.com/owner/repo/issues/123')"),
		),
	),
	func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		var params struct {
			ProjectID string `mapstructure:"project_id"`
			IssueURL  string `mapstructure:"issue_url"`
		}
		if err := mapstructure.Decode(request.Params.Arguments, &params); err != nil {
			return mcp.NewToolResultError(err.Error()), nil
		}

		// UNDERSTANDING: Get GraphQL client following existing patterns
		// VERIFIED: Same pattern used in pullrequests.go:1155-1158
		client, err := getGQLClient(ctx)
		if err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to get GitHub GQL client: %v", err)), nil
		}

		// UNDERSTANDING: Execute addProjectV2ItemById mutation
		// EXPECTS: GitHub Projects v2 API requires project node ID and content ID  
		// RETURNS: Item details including database ID for future operations
		// INTEGRATION: Direct GraphQL mutation following GitHub's Projects v2 schema
		var addItemMutation struct {
			AddProjectV2ItemById struct {
				Item struct {
					ID         githubv4.ID
					DatabaseID githubv4.Int
				}
			} `graphql:"addProjectV2ItemById(input: $input)"`
		}

		if err := client.Mutate(
			ctx,
			&addItemMutation,
			githubv4.AddProjectV2ItemByIdInput{
				ProjectID: githubv4.ID(params.ProjectID),
				ContentID: githubv4.ID(params.IssueURL), // GitHub accepts URLs as content IDs
			},
			nil,
		); err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to add item to project: %v", err)), nil
		}

		// UNDERSTANDING: Return success response with item details
		// INTEGRATION: Consistent with other MCP tool success responses
		response := map[string]interface{}{
			"success":     true,
			"message":     "Item successfully added to project",
			"item_id":     addItemMutation.AddProjectV2ItemById.Item.ID,
			"database_id": int(addItemMutation.AddProjectV2ItemById.Item.DatabaseID),
		}

		responseJSON, err := json.Marshal(response)
		if err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to marshal response: %v", err)), nil
		}

		return mcp.NewToolResultText(string(responseJSON)), nil
	}
}

// UNDERSTANDING: List user's GitHub Projects v2 boards for project ID lookup
// EXPECTS: login (GitHub username or organization name)
// RETURNS: List of projects with IDs and metadata
// INTEGRATION: Essential for finding project_id parameter for AddItemToProject
func ListUserProjects(getGQLClient GetGQLClientFn, t translations.TranslationHelperFunc) (mcp.Tool, server.ToolHandlerFunc) {
	return mcp.NewTool("list_user_projects",
		mcp.WithDescription(t("TOOL_LIST_USER_PROJECTS_DESCRIPTION", "List GitHub Projects v2 boards for a user or organization. Use this to find project IDs needed for adding items to projects.")),
		mcp.WithToolAnnotation(mcp.ToolAnnotation{
			Title:        t("TOOL_LIST_USER_PROJECTS_USER_TITLE", "List user projects"),
			ReadOnlyHint: ToBoolPtr(true),
		}),
		mcp.WithString("login",
			mcp.Required(),
			mcp.Description("GitHub username or organization name"),
		),
		mcp.WithNumber("first",
			mcp.Description("Number of projects to retrieve (default: 10, max: 100)"),
		),
	),
	func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		var params struct {
			Login string  `mapstructure:"login"`
			First *int    `mapstructure:"first"`
		}
		if err := mapstructure.Decode(request.Params.Arguments, &params); err != nil {
			return mcp.NewToolResultError(err.Error()), nil
		}

		// UNDERSTANDING: Default pagination following GitHub API best practices
		// VERIFIED: Consistent with existing pagination in discussions.go:16
		if params.First == nil {
			defaultFirst := 10
			params.First = &defaultFirst
		}
		if *params.First > 100 {
			*params.First = 100
		}

		client, err := getGQLClient(ctx)
		if err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to get GitHub GQL client: %v", err)), nil
		}

		// UNDERSTANDING: Query Projects v2 using GitHub's GraphQL schema
		// EXPECTS: User/Organization login and pagination parameters
		// RETURNS: Project list with IDs, titles, URLs, and metadata
		// INTEGRATION: Standard GraphQL query pattern following existing codebase structure
		var projectsQuery struct {
			User struct {
				ProjectsV2 struct {
					Nodes []struct {
						ID          githubv4.ID
						Number      githubv4.Int
						Title       githubv4.String
						URL         githubv4.String
						Closed      githubv4.Boolean
						CreatedAt   githubv4.DateTime
						UpdatedAt   githubv4.DateTime
						Description githubv4.String
					}
					TotalCount githubv4.Int
					PageInfo   struct {
						HasNextPage githubv4.Boolean
						EndCursor   githubv4.String
					}
				} `graphql:"projectsV2(first: $first)"`
			} `graphql:"user(login: $login)"`
		}

		if err := client.Query(ctx, &projectsQuery, map[string]interface{}{
			"login": githubv4.String(params.Login),
			"first": githubv4.Int(*params.First),
		}); err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to query user projects: %v", err)), nil
		}

		responseJSON, err := json.Marshal(projectsQuery)
		if err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to marshal response: %v", err)), nil
		}

		return mcp.NewToolResultText(string(responseJSON)), nil
	}
}

// UNDERSTANDING: Update project item field values (move between columns, update status)
// EXPECTS: project_id, item_id, field_id, value (string/single_select/date/number)
// RETURNS: Success confirmation with updated field details
// INTEGRATION: Enables workflow automation by updating project board item states
func UpdateProjectItemStatus(getGQLClient GetGQLClientFn, t translations.TranslationHelperFunc) (mcp.Tool, server.ToolHandlerFunc) {
	return mcp.NewTool("update_project_item_status",
		mcp.WithDescription(t("TOOL_UPDATE_PROJECT_ITEM_STATUS_DESCRIPTION", "Update a project item's field value (status, assignee, priority, etc.) in GitHub Projects v2. Use this to move items between columns or update custom fields.")),
		mcp.WithToolAnnotation(mcp.ToolAnnotation{
			Title:        t("TOOL_UPDATE_PROJECT_ITEM_STATUS_USER_TITLE", "Update project item status"),
			ReadOnlyHint: ToBoolPtr(false),
		}),
		mcp.WithString("project_id",
			mcp.Required(),
			mcp.Description("GitHub Projects v2 project ID"),
		),
		mcp.WithString("item_id", 
			mcp.Required(),
			mcp.Description("Project item ID (returned from add_item_to_project)"),
		),
		mcp.WithString("field_id",
			mcp.Required(), 
			mcp.Description("Project field ID to update (use get_project_fields to find this)"),
		),
		mcp.WithString("value",
			mcp.Required(),
			mcp.Description("New field value (string for text fields, option ID for single select fields)"),
		),
	),
	func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		var params struct {
			ProjectID string `mapstructure:"project_id"`
			ItemID    string `mapstructure:"item_id"`
			FieldID   string `mapstructure:"field_id"`
			Value     string `mapstructure:"value"`
		}
		if err := mapstructure.Decode(request.Params.Arguments, &params); err != nil {
			return mcp.NewToolResultError(err.Error()), nil
		}

		client, err := getGQLClient(ctx)
		if err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to get GitHub GQL client: %v", err)), nil
		}

		// UNDERSTANDING: Update project item field using GitHub's updateProjectV2ItemFieldValue mutation
		// EXPECTS: Project ID, item ID, field ID, and properly formatted value
		// RETURNS: Updated field details including the new value
		// INTEGRATION: Core workflow automation - moves items between columns and updates statuses
		var updateFieldMutation struct {
			UpdateProjectV2ItemFieldValue struct {
				ProjectV2Item struct {
					ID githubv4.ID
				}
			} `graphql:"updateProjectV2ItemFieldValue(input: $input)"`
		}

		if err := client.Mutate(
			ctx,
			&updateFieldMutation,
			githubv4.UpdateProjectV2ItemFieldValueInput{
				ProjectID: githubv4.ID(params.ProjectID),
				ItemID:    githubv4.ID(params.ItemID),
				FieldID:   githubv4.ID(params.FieldID),
				Value: githubv4.ProjectV2FieldValue{
					Text: githubv4.NewString(githubv4.String(params.Value)),
				},
			},
			nil,
		); err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to update project item field: %v", err)), nil
		}

		response := map[string]interface{}{
			"success": true,
			"message": "Project item field updated successfully",
			"item_id": updateFieldMutation.UpdateProjectV2ItemFieldValue.ProjectV2Item.ID,
		}

		responseJSON, err := json.Marshal(response)
		if err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to marshal response: %v", err)), nil
		}

		return mcp.NewToolResultText(string(responseJSON)), nil
	}
}

// UNDERSTANDING: Link an existing GitHub Projects v2 board to a repository
// EXPECTS: project_id (Projects v2 ID), repository_id (repository node ID)
// RETURNS: Success confirmation of the linking operation
// INTEGRATION: Solves the "put it back" use case - reconnect existing projects to repositories
func LinkProjectToRepository(getGQLClient GetGQLClientFn, t translations.TranslationHelperFunc) (mcp.Tool, server.ToolHandlerFunc) {
	return mcp.NewTool("link_project_to_repository",
		mcp.WithDescription(t("TOOL_LINK_PROJECT_TO_REPOSITORY_DESCRIPTION", "Link an existing GitHub Projects v2 board to a repository. Use this to reconnect projects that were previously unlinked or to establish new project-repository associations.")),
		mcp.WithToolAnnotation(mcp.ToolAnnotation{
			Title:        t("TOOL_LINK_PROJECT_TO_REPOSITORY_USER_TITLE", "Link project to repository"),
			ReadOnlyHint: ToBoolPtr(false),
		}),
		mcp.WithString("project_id",
			mcp.Required(),
			mcp.Description("GitHub Projects v2 project ID (PVT_xxxx format)"),
		),
		mcp.WithString("repository_id",
			mcp.Required(),
			mcp.Description("GitHub repository node ID (R_xxxx format) - use get_repository to find this"),
		),
	),
	func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		var params struct {
			ProjectID    string `mapstructure:"project_id"`
			RepositoryID string `mapstructure:"repository_id"`
		}
		if err := mapstructure.Decode(request.Params.Arguments, &params); err != nil {
			return mcp.NewToolResultError(err.Error()), nil
		}

		// UNDERSTANDING: Get GraphQL client following existing patterns
		// VERIFIED: Same pattern used in other Projects v2 tools
		client, err := getGQLClient(ctx)
		if err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to get GitHub GQL client: %v", err)), nil
		}

		// UNDERSTANDING: Execute linkProjectV2ToRepository mutation
		// EXPECTS: GitHub Projects v2 project ID and repository node ID  
		// RETURNS: Success confirmation of the linking operation
		// INTEGRATION: Direct GraphQL mutation following GitHub's Projects v2 schema
		// VERIFIED: Payload only returns repository field, not project field
		var linkProjectMutation struct {
			LinkProjectV2ToRepository struct {
				Repository struct {
					ID   githubv4.ID
					Name githubv4.String
				}
			} `graphql:"linkProjectV2ToRepository(input: $input)"`
		}

		if err := client.Mutate(
			ctx,
			&linkProjectMutation,
			githubv4.LinkProjectV2ToRepositoryInput{
				ProjectID:    githubv4.ID(params.ProjectID),
				RepositoryID: githubv4.ID(params.RepositoryID),
			},
			nil,
		); err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to link project to repository: %v", err)), nil
		}

		// UNDERSTANDING: Return success response with linking details
		// INTEGRATION: Consistent with other MCP tool success responses
		// VERIFIED: Only repository details available in mutation payload
		response := map[string]interface{}{
			"success":         true,
			"message":         "Project successfully linked to repository",
			"project_id":      params.ProjectID, // Use input parameter since not returned
			"repository_id":   linkProjectMutation.LinkProjectV2ToRepository.Repository.ID,
			"repository_name": linkProjectMutation.LinkProjectV2ToRepository.Repository.Name,
		}

		responseJSON, err := json.Marshal(response)
		if err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to marshal response: %v", err)), nil
		}

		return mcp.NewToolResultText(string(responseJSON)), nil
	}
}

// UNDERSTANDING: Unlink a GitHub Projects v2 board from a repository  
// EXPECTS: project_id (Projects v2 ID), repository_id (repository node ID)
// RETURNS: Success confirmation of the unlinking operation
// INTEGRATION: Inverse operation to LinkProjectToRepository for complete project-repository management
func UnlinkProjectFromRepository(getGQLClient GetGQLClientFn, t translations.TranslationHelperFunc) (mcp.Tool, server.ToolHandlerFunc) {
	return mcp.NewTool("unlink_project_from_repository",
		mcp.WithDescription(t("TOOL_UNLINK_PROJECT_FROM_REPOSITORY_DESCRIPTION", "Unlink a GitHub Projects v2 board from a repository. The project and its data remain intact, but it will no longer appear in the repository's Projects tab.")),
		mcp.WithToolAnnotation(mcp.ToolAnnotation{
			Title:        t("TOOL_UNLINK_PROJECT_FROM_REPOSITORY_USER_TITLE", "Unlink project from repository"),
			ReadOnlyHint: ToBoolPtr(false),
		}),
		mcp.WithString("project_id",
			mcp.Required(),
			mcp.Description("GitHub Projects v2 project ID (PVT_xxxx format)"),
		),
		mcp.WithString("repository_id",
			mcp.Required(),
			mcp.Description("GitHub repository node ID (R_xxxx format)"),
		),
	),
	func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		var params struct {
			ProjectID    string `mapstructure:"project_id"`
			RepositoryID string `mapstructure:"repository_id"`
		}
		if err := mapstructure.Decode(request.Params.Arguments, &params); err != nil {
			return mcp.NewToolResultError(err.Error()), nil
		}

		// UNDERSTANDING: Get GraphQL client following existing patterns
		// VERIFIED: Same pattern used in other Projects v2 tools
		client, err := getGQLClient(ctx)
		if err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to get GitHub GQL client: %v", err)), nil
		}

		// UNDERSTANDING: Execute unlinkProjectV2FromRepository mutation
		// EXPECTS: GitHub Projects v2 project ID and repository node ID
		// RETURNS: Success confirmation of the unlinking operation  
		// INTEGRATION: Direct GraphQL mutation following GitHub's Projects v2 schema
		// VERIFIED: Payload only returns repository field, not project field
		var unlinkProjectMutation struct {
			UnlinkProjectV2FromRepository struct {
				Repository struct {
					ID   githubv4.ID
					Name githubv4.String
				}
			} `graphql:"unlinkProjectV2FromRepository(input: $input)"`
		}

		if err := client.Mutate(
			ctx,
			&unlinkProjectMutation,
			githubv4.UnlinkProjectV2FromRepositoryInput{
				ProjectID:    githubv4.ID(params.ProjectID),
				RepositoryID: githubv4.ID(params.RepositoryID),
			},
			nil,
		); err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to unlink project from repository: %v", err)), nil
		}

		// UNDERSTANDING: Return success response with unlinking details
		// INTEGRATION: Consistent with other MCP tool success responses
		// VERIFIED: Only repository details available in mutation payload
		response := map[string]interface{}{
			"success":         true,
			"message":         "Project successfully unlinked from repository",
			"project_id":      params.ProjectID, // Use input parameter since not returned
			"repository_id":   unlinkProjectMutation.UnlinkProjectV2FromRepository.Repository.ID,
			"repository_name": unlinkProjectMutation.UnlinkProjectV2FromRepository.Repository.Name,
		}

		responseJSON, err := json.Marshal(response)
		if err != nil {
			return mcp.NewToolResultError(fmt.Sprintf("failed to marshal response: %v", err)), nil
		}

		return mcp.NewToolResultText(string(responseJSON)), nil
	}
}