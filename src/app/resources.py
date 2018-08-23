import datetime

from flask import make_response, request, session as sess
from flask_restplus import Resource
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from . import app, api
from .base import Session
from .models import User, Password
from .scheme import UserSchema, PasswordSchema, SearchSchema, SearchPasswordUrlSchema
from .swagger_models import user_post, password_api_model, user_login, user_put, search_password, search_password_url

session = Session()


@app.before_request
def require_login():
    """
    Require login function will be run before each request.
    The function will be called without any arguments. This function checks whether requested route is allowed to
    unregistered user or not in allowed routes. Also, checks if session isn't empty. Otherwise, it will return 403 error

    """
    allowed_routes = ['login', 'register', 'home', 'doc', 'restplus_doc.static', 'specs']
    if request.endpoint not in allowed_routes and 'email' not in sess:
        return make_response('You are not allowed to use this resource without logging in!', 403)


# GENERAL RESOURCES:
# Home,
# Smoke,
# Login,
# Logout,
# Register


@api.representation('/json')
class Home(Resource):
    def get(self):
        return 'This is a Home Page', 200  # OK


@api.representation('/json')
class Smoke(Resource):
    def get(self):
        return 'OK', 200  # OK


@api.representation('/json')
class Login(Resource):
    """
    Login resource.
    Checks whether entered data is in DB. Create user session based on its id and then sets session lifetime.
    Otherwise, it will return 401 error.
    """

    @api.expect(user_login)
    def post(self):
        data = request.get_json()
        user = User.filter_by_email(data['email'], session)
        if user and user.compare_hash(data['password']):
            sess['email'] = data['email']
            sess.permanent = True
            app.permanent_session_lifetime = datetime.timedelta(minutes=60)
            return f'You are LOGGED IN as {user.email}'
        return 'Could not verify your login!', 401, {"WWW-Authenticate": 'Basic realm="Login Required"'}


@api.representation('/json')
class Logout(Resource):
    """
    Logout resource.
    Remove the username from the session.
    """

    def get(self):
        sess.pop('email', None)
        return 'Dropped!', 200  # OK


@api.representation('/json')
class Register(Resource):
    """
    Register resource.
    Parsing requested data, checks if username or email doesn't exit in DB, then create user in DB. 200 OK
    Otherwise, return 500 or 400 error.
    """

    @api.expect(user_post)
    def post(self):
        json_data = request.get_json()
        if not json_data or not isinstance(json_data, dict):
            return 'No input data provided', 400  # Bad Request
        print(json_data)

        # Validate and deserialize input
        try:
            data = UserSchema().load(json_data)
        except ValidationError as err:
            return str(err), 422  # Unprocessable Entity
        print(data)
        # TODO One function for all
        # Check if a new user is not exist in data base
        if session.query(User).filter(User.username == data['username']).first():
            return f"User with username: {data['username']} is ALREADY EXISTS.", 200  # OK
        elif session.query(User).filter(User.email == data['email']).first():
            return f"User with email: {data['email']} is ALREADY EXISTS.", 200  # OK
        else:
            # crate a new user
            try:
                session.add(User(data))
                session.commit()
                return f"USER {data['username']} ADDED", 200  # OK
            except SQLAlchemyError as err:
                return str(err), 500  # Internal Server Error


# RESOURCES FOR REGISTERED USER:
# UserResource,
# UserPasswordResource,
# UserPasswordSearchResource,
# UserPasswordLinkResource,
# UserPasswordNumberResource


@api.representation('/json')
class UserResource(Resource):
    """User resource

    Works with user's general data.

    Methods:
        GET - get user's data,
        PUT - update user's data,
        DELETE - remove user with his data.
    """
    def get(self):
        current_user_email = sess.get('email', 'not set')
        try:
            user_data = User.filter_by_email(current_user_email, session)
        except SQLAlchemyError as err:
            return str(err), 500
        return UserSchema().dump(user_data), 200

    @api.expect(user_put)
    def put(self):
        current_user_email = sess.get('email', 'not set')
        args = request.get_json()
        try:
            current_user = User.filter_by_email(current_user_email, session)
            for arg_key in args.keys():
                if arg_key != 'password':
                    current_user.__setattr__(arg_key, args[arg_key])
            session.add(current_user)
            session.commit()
            return f'User {current_user.username} UPDATED', 200
        except SQLAlchemyError as err:
            return err, 500

    def delete(self):
        current_user_email = sess.get('email', 'not set')
        try:
            current_user = User.filter_by_email(current_user_email, session)
            session.query(User).filter(User.email == current_user_email).delete()
            session.commit()
            return f'User {current_user.username} DELETED', 200
        except SQLAlchemyError as err:
            return str(err), 500


# Please, write here the UserPasswordResource class
@api.representation('/json')
class UserPasswordsResource(Resource):
    """
    User password resource.

    User gets his all passwords and may create a new one.
    """

    def get(self):
        """
        Get list of user's passwords.

        User defines by sess email, returns a list of passwords for current logged in user.
        :return: list of passwords or 500 SQLAlchemyError
        """
        try:
            current_user_email = sess.get('email')
            current_user = User.filter_by_email(current_user_email, session)
            passwords = session.query(Password).filter(Password.user_id == current_user.id).all()
            passwords_serialized = []
            for password in passwords:
                passwords_serialized.append(password.serialize)
            return {'Your passwords': passwords_serialized}, 200  # OK
        except SQLAlchemyError as err:
            return str(err), 500  # Internal Server Error

    @api.expect(password_api_model)
    def post(self):
        """
        Create a new user's password.

        Create a new password for current logged in user, without specifying any parameters.
        :return: 200 OK or 500 SQLAlchemyError
        """
        json_data = request.get_json()
        if not json_data or not isinstance(json_data, dict):
            return 'No input data provided', 400  # Bad Request

        # Validate and deserialize input
        try:
            data = PasswordSchema().load(json_data)
        except ValidationError as err:
            return str(err), 422  # Unprocessable Entity

        current_user_email = sess.get('email', 'not set')
        current_user = User.filter_by_email(current_user_email, session)

        # create a new password
        try:
            session.add(Password(current_user.id, data))
            session.commit()
            return 'PASSWORD ADDED', 200  # OK
        except SQLAlchemyError as err:
            return str(err), 500  # Internal Server Error


# Please, write here the UserPasswordSearchResource class
@api.representation('/json')
class UserPasswordsSearchResource(Resource):
    """
    Search for particular passwords using password's description
    """

    @api.expect(search_password)
    def post(self):
        """
        Search for passwords by its description.

        Get json data, tries to find any matches in current logged in user list of passwords by its title and comment.
        :return: list with passwords that fit or 404 Error or 400 if no data provided or 422 ValidationError
        """
        json_data = request.get_json()
        if not json_data or not isinstance(json_data, dict):
            return 'No input data provided', 400  # Bad Request

        # Validate and deserialize input
        try:
            data = SearchSchema().load(json_data)
        except ValidationError as err:
            return str(err), 422  # Unprocessable Entity
        current_user_email = sess.get('email', 'not set')
        current_user = User.filter_by_email(current_user_email, session)
        all_passwords = session.query(Password).filter(Password.user_id == current_user.id).all()
        filtered_passwords = list()
        for password in all_passwords:
            if data.get("condition") in password.title or data.get("condition") in password.comment:
                filtered_passwords.append(password.serialize)

        if filtered_passwords:
            return filtered_passwords
        else:
            return 'No matches found', 404


# Please, write here the UserPasswordLinkResource class
@api.representation('/json')
class UserPasswordsSearchUrlResource(Resource):
    """User Passwords Search URL resource

    Methods:
        POST - send condition for searching and get user's passwords by URL.
    """
    @api.expect(search_password_url)
    def post(self):
        json_data = request.get_json()

        if not json_data or not isinstance(json_data, dict):
            return 'No input data provided', 400
        # Input data validation by Marshmallow schema
        try:
            data = SearchPasswordUrlSchema().load(json_data)
        except ValidationError as err:
            return str(err), 422

        current_user_email = sess.get('email', 'not set')

        try:
            current_user = User.filter_by_email(current_user_email, session)
            # Hard search without wildcard percent sign
            filtered_passwords = session.query(Password).filter(Password.user_id == current_user.id,
                                                                Password.url.like(f'{data.get("url")}'))
        except SQLAlchemyError as err:
            return str(err), 500

        passwords_by_url = []
        for password in filtered_passwords:
            passwords_by_url.append(password.serialize)
        if passwords_by_url:
            return passwords_by_url, 200
        else:
            return 'No matches found', 200


# Please, write here the UserPasswordNumberResource class
@api.representation('/json')
class UserPasswordsNumberResource(Resource):
    """
    Class for dealing with user's passwords.

    User can get a password by id, update password by id and delete password by id.
    """

    def get(self, pass_id):
        """
        Get particular password by pass_id

        Get password from current logged in user by pass_id.
        :param pass_id: id of specific user's password
        :return: password or 500 SQLAlchemyError
        """
        try:
            current_user_email = sess.get('email', 'not set')
            current_user = User.filter_by_email(current_user_email, session)
            password = Password.find_pass(current_user.id, pass_id, session)
            if not password:
                return 'Password Not Found', 404  # Not Found
            return {'password': password.serialize}, 200  # OK
        except SQLAlchemyError as err:
            return str(err), 500  # Internal Server Error

    @api.expect(password_api_model)
    def put(self, pass_id):
        """
        Update password data.

        You can update all data of password or just a part of it.
        :param pass_id: id of password data you'd like to update of
        :return: 200 OK or 500 SQLAlchemyError
        """
        json_data = request.get_json()
        try:
            data = PasswordSchema().load(json_data)
        except ValidationError as err:
            return str(err), 422  # Unprocessable Entity
        try:
            if not Password.is_password_exists(pass_id):
                return 'Password Not Found', 404
            password = Password.filter_pass_by_id(pass_id, session)
            previous_pass = password.title

            for arg_key in data.keys():
                if arg_key != 'password':
                    password.__setattr__(arg_key, data[arg_key])
                else:
                    password.crypt_password(data[arg_key])
            session.add(password)
            session.commit()
            return f'Data for {previous_pass} has been updated successfully', 200
        except SQLAlchemyError as err:
            return str(err), 500

    def delete(self, pass_id):
        """
        Delete specific password

        Delete password from current logged in user by pass_id.
        :param pass_id: id of specific user's password
        :return: 200 OK or 404 Password Not Found or 500 SQLAlchemyError
        """
        try:
            current_user_email = sess.get('email', 'not set')
            current_user = User.filter_by_email(current_user_email, session)
            password = Password.find_pass(current_user.id, pass_id, session)
            if password:
                session.query(Password) \
                    .filter(Password.user_id == current_user.id) \
                    .filter(Password.pass_id == pass_id) \
                    .delete()
                session.commit()
                return f'Password ID {pass_id} DELETED', 200  # OK
            else:
                return 'Password Not Found', 404  # Not Found
        except SQLAlchemyError as err:
            return str(err), 500  # Internal Server Error


# RESOURCES FOR ADMIN:
# Please, write here your admin resources list


@api.representation('/json')
class AdminUsersListResource(Resource):
    def get(self):
        try:
            users = session.query(User).all()
        except SQLAlchemyError as err:
            return str(err), 500  # Internal Server Error
        return UserSchema(many=True).dump(users), 200  # OK


@api.representation('/json')
class AdminUsersResource(Resource):
    def get(self, user_id):
        try:
            user_data = User.filter_by_id(user_id, session)
        except SQLAlchemyError as err:
            return str(err), 500  # Internal Server Error
        if user_data:
            return UserSchema().dump(user_data), 200  # OK
        else:
            return f'User ID {user_id} - Not Found', 404  # Not Found

    @api.expect(user_put)
    def put(self, user_id):
        args = request.get_json()
        # TODO validation
        # if not json_data or not isinstance(json_data, dict):
        #     return 'No input data provided', 400  # Bad Request

        try:
            if not User.is_user_exists(user_id):
                return 'User not found', 404  # Not Found
            user = User.filter_by_id(user_id, session)
            for arg_key in args.keys():
                if arg_key != 'password':
                    user.__setattr__(arg_key, args[arg_key])
            session.add(user)
            session.commit()
            msg = f'User {user.username} with id {user_id} has been successfully updated.'
            return msg, 200  # OK
        except SQLAlchemyError as err:
            return err, 500  # Internal Server Error

    def delete(self, user_id):
        try:
            if User.filter_by_id(user_id, session):
                session.query(User).filter(User.id == user_id).delete()
                session.commit()
                return f'User ID:{user_id} has been DELETED.', 200  # OK
            else:
                return f'User ID {user_id} - Not Found', 404  # Not Found
        except SQLAlchemyError as err:
            return str(err), 500  # Internal Server Error


@api.representation('/json')
class PasswordListResource(Resource):
    @api.expect(password_api_model)
    def post(self, user_id):
        json_data = request.get_json()
        if not json_data or not isinstance(json_data, dict):
            return 'No input data provided', 400  # Bad Request

        # Validate and deserialize input
        try:
            data = PasswordSchema().load(json_data)
        except ValidationError as err:
            return str(err), 422  # Unprocessable Entity

        if not User.filter_by_id(user_id, session):
            return f'User ID {user_id} - Not Found', 404  # Not Found

        # crate a new password
        try:
            session.add(Password(user_id, data))
            session.commit()
            return 'PASSWORD ADDED', 200  # OK
        except SQLAlchemyError as err:
            return str(err), 500  # Internal Server Error

    def get(self, user_id):
        try:
            if not User.filter_by_id(user_id, session):
                return f'User ID {user_id} - Not Found', 404  # Not Found
            passwords = session.query(Password).filter(Password.user_id == user_id).all()
            passwords_serialized = []
            for password in passwords:
                passwords_serialized.append(password.serialize)
            return {'all user passwords': passwords_serialized}, 200  # OK
        except SQLAlchemyError as err:
            return str(err), 500  # Internal Server Error


@api.representation('/json')
class PasswordResource(Resource):
    def get(self, user_id, pass_id):
        try:
            if not User.filter_by_id(user_id, session):
                return f'User ID {user_id} - Not Found', 404  # Not Found
            password = session.query(Password) \
                .filter(Password.user_id == user_id) \
                .filter(Password.pass_id == pass_id) \
                .first()
            if not password:
                return 'Password Not Found', 404  # Not Found
            return {'password': password.serialize}, 200  # OK
        except SQLAlchemyError as err:
            return str(err), 500  # Internal Server Error

    @api.expect(password_api_model)
    def put(self, user_id, pass_id):
        args = request.get_json()
        # TODO validation
        try:
            if not User.is_user_exists(user_id):
                return 'User not found', 404
            if not Password.is_password_exists(pass_id):
                return 'Password not found', 404
            password = session.query(Password).filter(Password.pass_id == pass_id).first()

            for arg_key in args.keys():
                if arg_key != 'password':
                    password.__setattr__(arg_key, args[arg_key])
                else:
                    password.crypt_password(args[arg_key])
            session.add(password)
            session.commit()
            return f'Data of password with id{pass_id} has been updated successfully', 200
        except SQLAlchemyError as err:
            return str(err), 500

    def delete(self, user_id, pass_id):
        try:
            if not User.filter_by_id(user_id, session):
                return 'User Not Found', 404  # Not Found
            password = session.query(Password) \
                .filter(Password.user_id == user_id) \
                .filter(Password.pass_id == pass_id) \
                .first()
            if password:
                session.query(Password) \
                    .filter(Password.user_id == user_id) \
                    .filter(Password.pass_id == pass_id) \
                    .delete()
                session.commit()
                return f'Password ID {pass_id} DELETED', 200  # OK
            else:
                return 'Password Not Found', 404  # Not Found
        except SQLAlchemyError as err:
            return str(err), 500  # Internal Server Error


@api.representation('/json')
class UserSearch(Resource):
    def get(self, username):
        try:
            user_data = User.filter_by_username(username, session)
        except SQLAlchemyError as err:
            return str(err), 500  # Internal Server Error
        if user_data:
            return UserSchema().dump(user_data), 200  # OK
        else:
            return 'User not found', 404  # Not Found
