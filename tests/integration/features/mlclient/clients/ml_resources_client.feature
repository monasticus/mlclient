Feature: Test MLResourcesClient

  Scenario: Test /v1/eval endpoint

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

  Scenario: Test /manage/v2/logs endpoint (ErrorLog.txt)

    Given I initialized an MLResourcesClient's connection
    And I produce 10 test logs
      """
      Test Log <i>
      """
    And I wait 1 second(s)
    When I get error logs
      | start_time | regex           |
      | <today>    | Test Log .{1,2} |
    Then I get a successful response
    And I find produced logs