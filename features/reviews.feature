Feature: Review Management
  As a registered user
  I want to create, edit, and delete reviews
  So that I can interact with the community

  Background:
    Given an existing user "testuser" with password "pass1234"
    And an existing user "hacker" with password "pass1234"
    And an existing game titled "Super Mario"

  Scenario: Create a new review
    Given I log in with username "testuser" and password "pass1234"
    When I view the game "Super Mario" details
    And I fill in the add review form with "Amazing game!" and rating "5"
    And I click the publish button
    Then I should see "Amazing game!" in the reviews list

  Scenario: Edit an existing review
    Given the user "testuser" has a review with content "Good game" and rating "4" for "Super Mario"
    And I log in with username "testuser" and password "pass1234"
    When I view the game "Super Mario" details
    And I update my review to "Actually, it is a masterpiece!"
    Then I should see "Actually, it is a masterpiece!" in the reviews list

  Scenario: Delete an existing review
    Given the user "testuser" has a review with content "Terrible game" and rating "1" for "Super Mario"
    And I log in with username "testuser" and password "pass1234"
    When I view the game "Super Mario" details
    And I click the Delete button for my review
    Then I should not see "Terrible game" in the reviews list

  Scenario: Security restriction - Cannot edit another user's review
    Given the user "testuser" has a review with content "My private review" and rating "5" for "Super Mario"
    And I log in with username "hacker" and password "pass1234"
    When I view the game "Super Mario" details
    Then I should see "My private review" in the reviews list
    But I should not see the Edit or Delete buttons