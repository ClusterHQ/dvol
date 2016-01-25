Feature: Using dvol volumes with Docker containers

  Scenario Outline: implicit volume creation
    Given docker daemon is running
    And dvol volume plugin is installed
    When a container is created with a dvol volume named <name>
    Then a dvol volume repository named <name> exists
    And the active branch of the dvol volume repository named <name> is master
    And container has the tree of the active branch of the dvol volume repository named <name> mounted as its volume

    Examples: User-Facing
      | name    |
      | apples  |
      | bananas |

    Examples: Opaque
      | name                                                             |
      | 044fef43ba66fb924531d2d0cb241dd3fe81b980bc6ec475702afc6347f9caa8 |

  Scenario: volume re-use
    Given docker is running
    And dvol volume plugin is installed
    And a dvol volume named <name> already exists with a data file
      """
      Hello, world.
      """
    When a container is created with a dvol volume named <name>
    Then the container has a volume containing the data file
