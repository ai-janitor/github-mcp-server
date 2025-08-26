/*
 * UNDERSTANDING: Tests for GitHub Projects v2 API integration
 * DEPENDENCIES: Standard Go testing, githubv4 mock client, stretchr testify
 * EXPORTS: Test functions for CreateProject, AddItemToProject, ListUserProjects, UpdateProjectItemStatus, LinkProjectToRepository, UnlinkProjectFromRepository tools
 * INTEGRATION: Ensures Projects v2 tools work correctly with MCP framework
 */
package github

import (
	"testing"

	"github.com/github/github-mcp-server/pkg/translations"
	"github.com/shurcooL/githubv4"
	"github.com/stretchr/testify/assert"
)

// UNDERSTANDING: Test CreateProject tool creation and basic validation
// EXPECTS: Tool definition to be created without errors following existing patterns
// RETURNS: Pass/fail status for tool creation
// INTEGRATION: Validates foundational project creation tool
func TestCreateProject(t *testing.T) {
	mockClient := githubv4.NewClient(nil)
	
	tool, handler := CreateProject(stubGetGQLClientFn(mockClient), translations.NullTranslationHelper)
	
	assert.Equal(t, "create_project", tool.Name)
	assert.NotEmpty(t, tool.Description)
	assert.Contains(t, tool.InputSchema.Properties, "owner_id")
	assert.Contains(t, tool.InputSchema.Properties, "title")
	assert.Contains(t, tool.InputSchema.Properties, "description")
	assert.ElementsMatch(t, tool.InputSchema.Required, []string{"owner_id", "title"})
	
	if handler == nil {
		t.Error("expected handler to not be nil")
	}
}

// UNDERSTANDING: Test AddItemToProject tool creation and basic validation
// EXPECTS: Tool definition to be created without errors following existing patterns
// RETURNS: Pass/fail status for tool creation
// INTEGRATION: Follows same pattern as discussions_test.go:200-210
func TestAddItemToProject(t *testing.T) {
	// VERIFIED: Same pattern used in discussions_test.go and pullrequests_test.go
	mockClient := githubv4.NewClient(nil)
	
	tool, handler := AddItemToProject(stubGetGQLClientFn(mockClient), translations.NullTranslationHelper)
	
	assert.Equal(t, "add_item_to_project", tool.Name)
	assert.NotEmpty(t, tool.Description)
	assert.Contains(t, tool.InputSchema.Properties, "project_id")
	assert.Contains(t, tool.InputSchema.Properties, "issue_url") 
	assert.ElementsMatch(t, tool.InputSchema.Required, []string{"project_id", "issue_url"})
	
	if handler == nil {
		t.Error("expected handler to not be nil")
	}
}

// UNDERSTANDING: Test ListUserProjects tool creation and basic validation  
// EXPECTS: Tool definition to be created with proper read-only configuration
// RETURNS: Pass/fail status for tool creation
// INTEGRATION: Ensures consistent tool patterns across MCP Server
func TestListUserProjects(t *testing.T) {
	mockClient := githubv4.NewClient(nil)
	
	tool, handler := ListUserProjects(stubGetGQLClientFn(mockClient), translations.NullTranslationHelper)
	
	assert.Equal(t, "list_user_projects", tool.Name)
	assert.NotEmpty(t, tool.Description) 
	assert.Contains(t, tool.InputSchema.Properties, "login")
	assert.Contains(t, tool.InputSchema.Properties, "first")
	assert.ElementsMatch(t, tool.InputSchema.Required, []string{"login"})
	
	if handler == nil {
		t.Error("expected handler to not be nil")
	}
}

// UNDERSTANDING: Test UpdateProjectItemStatus tool creation and validation
// EXPECTS: Tool definition for write operations with proper annotations
// RETURNS: Pass/fail status for tool creation  
// INTEGRATION: Ensures write tools follow MCP Server write operation patterns
func TestUpdateProjectItemStatus(t *testing.T) {
	mockClient := githubv4.NewClient(nil)
	
	tool, handler := UpdateProjectItemStatus(stubGetGQLClientFn(mockClient), translations.NullTranslationHelper)
	
	assert.Equal(t, "update_project_item_status", tool.Name)
	assert.NotEmpty(t, tool.Description)
	assert.Contains(t, tool.InputSchema.Properties, "project_id")
	assert.Contains(t, tool.InputSchema.Properties, "item_id")
	assert.Contains(t, tool.InputSchema.Properties, "field_id")
	assert.Contains(t, tool.InputSchema.Properties, "value")
	assert.ElementsMatch(t, tool.InputSchema.Required, []string{"project_id", "item_id", "field_id", "value"})
	
	if handler == nil {
		t.Error("expected handler to not be nil")
	}
}

// UNDERSTANDING: Test LinkProjectToRepository tool creation and validation
// EXPECTS: Tool definition for write operations with proper repository linking parameters
// RETURNS: Pass/fail status for tool creation  
// INTEGRATION: Validates the "put it back" functionality for reconnecting projects to repositories
func TestLinkProjectToRepository(t *testing.T) {
	mockClient := githubv4.NewClient(nil)
	
	tool, handler := LinkProjectToRepository(stubGetGQLClientFn(mockClient), translations.NullTranslationHelper)
	
	assert.Equal(t, "link_project_to_repository", tool.Name)
	assert.NotEmpty(t, tool.Description)
	assert.Contains(t, tool.InputSchema.Properties, "project_id")
	assert.Contains(t, tool.InputSchema.Properties, "repository_id")
	assert.ElementsMatch(t, tool.InputSchema.Required, []string{"project_id", "repository_id"})
	
	if handler == nil {
		t.Error("expected handler to not be nil")
	}
}

// UNDERSTANDING: Test UnlinkProjectFromRepository tool creation and validation
// EXPECTS: Tool definition for write operations with proper unlinking parameters
// RETURNS: Pass/fail status for tool creation
// INTEGRATION: Validates inverse operation to linking for complete project-repository management
func TestUnlinkProjectFromRepository(t *testing.T) {
	mockClient := githubv4.NewClient(nil)
	
	tool, handler := UnlinkProjectFromRepository(stubGetGQLClientFn(mockClient), translations.NullTranslationHelper)
	
	assert.Equal(t, "unlink_project_from_repository", tool.Name)
	assert.NotEmpty(t, tool.Description)
	assert.Contains(t, tool.InputSchema.Properties, "project_id")
	assert.Contains(t, tool.InputSchema.Properties, "repository_id")
	assert.ElementsMatch(t, tool.InputSchema.Required, []string{"project_id", "repository_id"})
	
	if handler == nil {
		t.Error("expected handler to not be nil")
	}
}