from mlclient.model import Permission


def test_permissions_are_equal():
    assert Permission("role-1", {Permission.READ}) == Permission("role-1", {Permission.READ})


def test_permissions_are_not_equal():
    assert Permission("role-1", {Permission.READ}) != Permission("role-2", {Permission.READ})
    assert Permission("role-1", {Permission.READ}) != Permission("role-1", {Permission.UPDATE})
    assert Permission("role-1", {Permission.READ}) != Permission("role-2", {Permission.UPDATE})


def test_permissions_hashes_are_equal():
    assert Permission("role-1", {Permission.READ}).__hash__() == Permission("role-1", {Permission.READ}).__hash__()


def test_permissions_hashes_are_not_equal():
    assert Permission("role-1", {Permission.READ}).__hash__() != Permission("role-2", {Permission.READ}).__hash__()
    assert Permission("role-1", {Permission.READ}).__hash__() != Permission("role-1", {Permission.UPDATE}).__hash__()
    assert Permission("role-1", {Permission.READ}).__hash__() != Permission("role-2", {Permission.UPDATE}).__hash__()


def test_str():
    permission = Permission("custom-role", {Permission.READ})
    assert str(permission) == "Permission(role_name='custom-role', capabilities={'read'})"


def test_role_name():
    permission = Permission("custom_role", {Permission.READ})
    assert permission.role_name() == "custom_role"


def test_capabilities():
    capabilities = {Permission.READ, Permission.INSERT, Permission.UPDATE, Permission.UPDATE_NODE, Permission.EXECUTE}
    permission = Permission("custom_role", capabilities)
    assert permission.capabilities() == capabilities


def test_wrong_capabilities():
    capabilities = {Permission.READ, "ANY"}
    permission = Permission("custom_role", capabilities)
    assert permission.capabilities() == {Permission.READ}


def test_add_capability():
    permission = Permission("custom_role", set())
    success = permission.add_capability(Permission.READ)
    assert success is True
    assert permission.capabilities() == {Permission.READ}

    success = permission.add_capability(Permission.UPDATE)
    assert success is True
    assert permission.capabilities() == {Permission.READ, Permission.UPDATE}


def test_add_wrong_capability():
    permission = Permission("custom_role", set())
    success = permission.add_capability("ANY")
    assert success is False
    assert permission.capabilities() == set()


def test_add_capability_when_exists():
    permission = Permission("custom_role", {Permission.READ})
    success = permission.add_capability(Permission.READ)
    assert success is False
    assert permission.capabilities() == {Permission.READ}


def test_add_none_capability():
    permission = Permission("custom_role", {Permission.READ})
    success = permission.add_capability(None)
    assert success is False
    assert permission.capabilities() == {Permission.READ}


def test_remove_capability():
    permission = Permission("custom_role", {Permission.READ, Permission.UPDATE})
    success = permission.remove_capability(Permission.READ)
    assert success is True
    assert permission.capabilities() == {Permission.UPDATE}

    success = permission.remove_capability(Permission.UPDATE)
    assert success is True
    assert permission.capabilities() == set()


def test_remove_capability_when_does_dot_exist():
    permission = Permission("custom_role", {Permission.READ})
    success = permission.remove_capability(Permission.UPDATE)
    assert success is False
    assert permission.capabilities() == {Permission.READ}


def test_to_json():
    permission = Permission("custom_role", {Permission.READ})
    assert permission.to_json() == {
        "role-name": "custom_role",
        "capabilities": [
            Permission.READ
        ]
    }
