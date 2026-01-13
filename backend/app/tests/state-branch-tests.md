test_branch_state_changes_differ
    """
    Test that state changes differ based on which branch is taken.

    Given: Story with 2 branches setting different state
    When: Take first choice (sets gold: 10)
    Then: story_state contains (gold:10)
    When: Take left branch (sets path="left")
    Then: story_state contains {"path": "left", gold:10}
    When: Undo and take right branch (sets path="right")
    Then: story_state contains {"path": "right", gold:10}
    """


    """
    Test that undo from a branch returns to branch point with all choices available.

    A (choice x)-> B: sets character story_state (evil)
    A (choice y)-> C: sets character story_state (good)
    B,C (both nodes converge to) -> D
    D (choice bad_guy only visible if evil)-> E
    D (choice good_guy only visible if good)-> F
    E,F (both nodes converge to) -> G

    Player path: A -> B -> D - E -> G
    Player undo at G to A
    Player path: A -> C -> D
    Player sees F
    

    Given: Story with 2 branches setting different state
    When: Take first branch ()
    Then: story_state contains (gold:10)
    When: Take left branch (sets character="evil")
    Then: story_state contains {"path": "left", gold:10}
    When: Undo and take right branch (sets path="right")
    Then: story_state contains {"path": "right", gold:10}
    Then: Both left and right choices are still available
    """
