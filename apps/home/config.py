
class ConfigData:
    INSPECTOR_NAME = 'John Doe'
    INSPECTION_TYPE = 'Routine'
    COMPANY_NAME = 'TSM Consultancy'
    VIDEO_LOCATION = r"C:\Users\DanielYeoh\Desktop\INC_video"
    DROPBOX_AUTH_TOKEN = "sl.B66RqCHZjybO75rDuhVLTDQ60MPt3IPfgTNuHWH1UwFB4bjaJ7KNTC3KrZe4GfDalxkDTVK-Jn7YGatjwJccfD9xkCmDjcih6ERt6JD6P_mGxgywCs-TXBY-C7Xg0R1FVAkU5pRr4SkZSNQDKqeJhdA"
    DISPLAY_CONF = False
    DROPBOX_APP_KEY = "cdfpmgml5cfi57b"
    DROPBOX_APP_SECRET = "w72llnccsaetyob"
    NO_OF_DEFECTS_SHOWN = 6 # If there are more than 6 defects, only the first 6 will be shown

    @classmethod
    def update_dropbox_auth_token(cls, new_token):
        cls.DROPBOX_AUTH_TOKEN = new_token
        cls._write_to_file()

    @classmethod
    def _write_to_file(cls):
        config_file_path = __file__
        
        with open(config_file_path, 'r') as file:
            lines = file.readlines()
        
        with open(config_file_path, 'w') as file:
            for line in lines:
                if line.strip().startswith('DROPBOX_AUTH_TOKEN'):
                    file.write(f'    DROPBOX_AUTH_TOKEN = "{cls.DROPBOX_AUTH_TOKEN}"\n')
                else:
                    file.write(line)

