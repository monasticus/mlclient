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
      | data_format | start_time | regex           |
      | json        | <today>    | Test Log .{1,2} |

    Then I get a successful response
    And I confirm returned error logs structure
    And I find produced logs
    And I close the connection


  Scenario: Test /manage/v2/logs endpoint (AccessLog.txt)

    Given I initialized an MLResourcesClient's connection
    And I produce 10 test logs
      """
      Test Log <i>
      """
    And I wait 1 second(s)

    When I get access logs
      | data_format |
      | json        |

    Then I get a successful response
    And I confirm returned access logs structure
    And I find requests producing logs
    And I close the connection


  Scenario: Test /manage/v2/logs endpoint (RequestLog.txt)

    Given I initialized an MLResourcesClient's connection

    When I get request logs
      | data_format |
      | json        |

    Then I get a successful response
    And I confirm returned request logs structure
    And I close the connection