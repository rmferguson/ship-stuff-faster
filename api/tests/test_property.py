"""
Property-based tests using Hypothesis.

These tests verify invariants that hold across a range of inputs, not just
specific examples. Use them for validation logic, encoding/decoding roundtrips,
and boundary conditions.

Hypothesis + pytest-django note: @given tests cannot use function-scoped fixtures
(like api_client) directly. Instead, create what you need inside the test body.
Use @pytest.mark.django_db(transaction=True) to reset the database between examples
when your test modifies the DB.

To add more property tests:
1. Import strategies from hypothesis.strategies (or hypothesis.extra.django)
2. Decorate with @given(strategy)
3. Create API clients and DB objects inside the test body (not via fixtures)
4. Write an assertion that must hold for any input from the strategy

Run with extra examples for thorough checking:
  HYPOTHESIS_PROFILE=ci pytest tests/test_property.py -v
"""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from rest_framework.test import APIClient

SIGNUP_URL = "/api/v1/auth/signup/"


class TestUserRegistrationProperties:
    """
    Property-based tests for user registration invariants.

    These tests check that registration behaves consistently across a wide
    range of valid and invalid inputs — not just the hand-picked examples
    in test_auth.py.
    """

    @given(password=st.text(min_size=1, max_size=7))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.django_db(transaction=True)
    def test_short_passwords_always_rejected(self, password):
        """
        Any password under 8 characters must be rejected.

        This is a security invariant: the minimum password length policy
        must hold for all inputs, not just the examples we think to test.
        """
        client = APIClient()
        response = client.post(
            SIGNUP_URL,
            {"email": "test@example.com", "password": password},
            format="json",
        )
        # Any password under 8 chars must be a 400
        assert response.status_code == 400, (
            f"Password {password!r} (len={len(password)}) should have been rejected "
            f"but got {response.status_code}"
        )

    @given(email=st.emails())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.django_db(transaction=True)
    def test_signup_never_crashes(self, email):
        """
        Signup endpoint must never return 5xx for any email input.

        Property: the server is always in a valid state after a signup attempt,
        regardless of the email address format provided.
        """
        client = APIClient()
        response = client.post(
            SIGNUP_URL,
            {"email": email, "password": "securepass123"},
            format="json",
        )
        assert response.status_code < 500, (
            f"Server error {response.status_code} for email {email!r}: {response.data}"
        )


@pytest.mark.django_db(transaction=True)
class TestEmailNormalizationProperties:
    """
    Property tests for email handling invariants.

    Uses django_db at the class level with transaction=True so each
    @given example gets a clean database state.
    """

    @given(
        local=st.text(
            min_size=1,
            max_size=64,
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="._%+-"),
        ),
        domain=st.text(
            min_size=2,
            max_size=32,
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-"),
        ),
        tld=st.text(
            min_size=2,
            max_size=6,
            alphabet=st.characters(whitelist_categories=("L",)),
        ),
    )
    @settings(
        max_examples=30,  # Fewer examples here — DB transactions are slow
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
    )
    def test_signup_never_returns_500_for_any_email_shape(self, local, domain, tld):
        """
        The signup endpoint must never return a 5xx for any plausible email shape.

        This is a robustness invariant: the API must fail gracefully (400) for
        invalid inputs, never with a server error.
        """
        client = APIClient()
        email = f"{local}@{domain}.{tld}"
        response = client.post(
            SIGNUP_URL,
            {"email": email, "password": "securepass123"},
            format="json",
        )
        assert response.status_code < 500, (
            f"Unexpected 5xx for email {email!r}: {response.status_code} {response.data}"
        )
