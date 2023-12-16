Feature: Test MLResourcesClient

  Scenario: Test eval method

    Given I initialized an MLResourcesClient's connection
    And I prepared the following xquery code
      """
      xquery version '1.0-ml';

      declare variable $element as element() external;

      <new-parent>{$element/child::element()}</new-parent>
      """
    And I set the following variables
      | element                   |
      | <parent><child/></parent> |
    When I evaluate the code
    Then I get a successful multipart response
      | text                              |
      | <new-parent><child/></new-parent> |
    And I close the connection
