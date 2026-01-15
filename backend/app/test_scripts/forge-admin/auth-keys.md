
FORGE_TEST_ADMIN_USERNAME=forge-test
FORGE_TEST_ADMIN_USER_EMAIL=forge-test@forgetest.com
FORGE_TEST_ADMIN_USER_PASSWORD=pooppoop

tinyfoot token for the above: 23ea4ff28b6ac46733e172d7f15e91ffc3c57b4d

Forgejo needs the word token included before the API key token in an authorization header, like this:

Authorization: token 65eaa9c8ef52460d22a93307fe0aee76289dc675

curl "http://localhost:3000/api/v1/repos/test1/test1/issues" \
    -H "accept: application/json" \
    -H "Authorization: token 65eaa9c8ef52460d22a93307fe0aee76289dc675" \
    -H "Content-Type: application/json" -d "{ \"body\": \"testing\", \"title\": \"test 20\"}" -i

As mentioned above, the token used is the same one you would use in the token= string in a GET request.


