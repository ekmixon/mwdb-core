import React, { useCallback, useContext, useEffect, useState } from "react";
import { Link, Route, Switch, useHistory, useParams } from "react-router-dom";

import api from "@mwdb-web/commons/api";
import { AuthContext } from "@mwdb-web/commons/auth";
import { View, getErrorMessage } from "@mwdb-web/commons/ui";

import ProfileDetails from "./Views/ProfileDetails";
import ProfileAPIKeys from "./Views/ProfileAPIKeys";
import ProfileCapabilities from "./Views/ProfileCapabilities";
import ProfileResetPassword from "./Views/ProfileResetPassword";
import ProfileGroup from "./Views/ProfileGroup";

export default function ProfileViews() {
    const auth = useContext(AuthContext);
    const history = useHistory();
    const user = useParams().user || auth.user.login;
    const [profile, setProfile] = useState();

    async function updateProfile() {
        try {
            const response = await api.getUserProfile(user);
            setProfile(response.data);
        } catch (error) {
            history.push({
                pathname: "/profile",
                state: { error: getErrorMessage(error) },
            });
        }
    }

    function GroupBreadcrumb() {
        const { group } = useParams();
        return `Group '${group}' details`;
    }

    function UserBreadcrumb() {
        const { user } = useParams();
        return `User '${user}' details`;
    }

    const getProfile = useCallback(updateProfile, [user]);

    useEffect(() => {
        getProfile();
    }, [getProfile]);

    if (!profile) return [];

    return (
        <View ident="profile">
            <Switch>
                <Route exact path="/profile" />
                <Route>
                    <nav aria-label="breadcrumb">
                        <ol className="breadcrumb">
                            <li className="breadcrumb-item">
                                <Link to="/profile">Profile</Link>
                            </li>
                            <li className="breadcrumb-item active">
                                <Switch>
                                    <Route path="/profile/capabilities">
                                        Capabilities
                                    </Route>
                                    <Route path="/profile/api-keys">
                                        API keys
                                    </Route>
                                    <Route path="/profile/reset-password">
                                        Reset password
                                    </Route>
                                    <Route path="/profile/group/:group">
                                        <GroupBreadcrumb />
                                    </Route>
                                    <Route path="/profile/user/:user">
                                        <UserBreadcrumb />
                                    </Route>
                                </Switch>
                            </li>
                        </ol>
                    </nav>
                </Route>
            </Switch>
            <Switch>
                <Route exact path={["/profile", "/profile/user/:user"]}>
                    <ProfileDetails profile={profile} />
                </Route>
                <Route exact path="/profile/group/:group">
                    <ProfileGroup profile={profile} />
                </Route>
                <Route exact path="/profile/capabilities">
                    <ProfileCapabilities profile={profile} />
                </Route>
                <Route exact path="/profile/api-keys">
                    <ProfileAPIKeys
                        profile={profile}
                        updateProfile={updateProfile}
                    />
                </Route>
                <Route exact path="/profile/reset-password">
                    <ProfileResetPassword profile={profile} />
                </Route>
            </Switch>
        </View>
    );
}
