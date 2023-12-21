Feature: Test MLResourceClient

  Scenario: Test a simple call

    Given I initialized an MLResourceClient's connection
    And I prepared the following xquery code to eval
      """
      xquery version '1.0-ml';

      declare variable $element as element() external;

      <new-parent>{$element/child::element()}</new-parent>
      """
    And I set the following variables for the code
      | element                   |
      | <parent><child/></parent> |
    When I call the EvalCall
    Then I get a successful multipart response
      | text                              |
      | <new-parent><child/></new-parent> |
    And I close the connection
