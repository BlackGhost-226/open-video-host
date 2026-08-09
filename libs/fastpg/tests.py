from messages import MessageBase

def test(test_bytes: bytes, message_class: MessageBase):
    print(message_class.__name__)
    print(message_class.matches(test_bytes))
    print(message_class.parse(test_bytes))
    print()

if __name__ == "__main__":
    from messages.simple.frontend import Query, SASLInitialResponse
    from messages.simple.backend import AuthenticationMD5Password, AuthenticationSASL, CopyInResponse, DataRow, NegotiateProtocolVersion, AuthenticationOk, ErrorResponse, BackendKeyData, FunctionCallResponse, ParameterDescription
    from messages.special import StartupMessage, CancelRequest
    
    query_test = b'Q\x00\x00\x00\x12SELECT 1;\x00'
    test(query_test, Query)

    sasl_test = b'p\x00\x00\x00#SCRAM-SHA-256\x00\x00\x00\x00\x0en=user,r=1234'
    test(sasl_test, SASLInitialResponse)

    startup_bytes = (
            b'\x00\x00\x00)'                  # Int32 Length: 41 bytes
            b'\x00\x03\x00\x00'              # Int32 Protocol Version: 3.0 (196608)
            b'user\x00postgres\x00'          # Key: 'user', Value: 'postgres'
            b'database\x00app_db\x00'        # Key: 'database', Value: 'app_db'
            b'\x00'                          # Trailing null terminator
        )
    test(startup_bytes, StartupMessage)

    cancel_bytes = (
            b'\x00\x00\x00\x10'              # Int32 Length: 16 bytes
            b'\x04\xd2\x16\x2e'              # Int32 Cancel Code: 80877102
            b'\x00\x00\x04\xd2'              # Int32 Process ID: 1234
            b'\x12\x34\x56\x78'              # Int32 Secret Key: 0x12345678 (305419896)
        )
    test(cancel_bytes, CancelRequest)

    auth_md5_bytes = b'R\x00\x00\x00\x0c\x00\x00\x00\x05\x12\x34\x56\x78'
    test(auth_md5_bytes, AuthenticationMD5Password)

    auth_sasl_bytes = (
            b'R\x00\x00\x00\x17'              # Tag 'R', Int32 Length: 23
            b'\x00\x00\x00\n'               # Int32 Auth Code: 10 (SASL)
            b'SCRAM-SHA-256\x00'            # Mechanism string + null byte
            b'\x00'                         # Trailing null terminator
        )
    test(auth_sasl_bytes, AuthenticationSASL)

    copy_in_bytes = (
            b'G\x00\x00\x00\x0b'     # Tag 'G', Int32 Length: 11
            b'\x00'                 # Int8 Format: 0 (Text)
            b'\x00\x02'             # Int16 Column Count: 2
            b'\x00\x00'             # Int16 Col 0 Format: 0 (Text)
            b'\x00\x00'             # Int16 Col 1 Format: 0 (Text)
        )
    test(copy_in_bytes, CopyInResponse)

    data_row_bytes = (
            b'D\x00\x00\x00\x17'     # Tag 'D', Int32 Length: 23
            b'\x00\x02'             # Int16 Column Count: 2
            # Column 1: 'hello' (length 5)
            b'\x00\x00\x00\x05'     # Int32 Col 1 Length: 5
            b'hello'                # Col 1 Value
            # Column 2: NULL (length -1)
            b'\xff\xff\xff\xff'     # Int32 Col 2 Length: -1 (NULL)
        )
    test(data_row_bytes, DataRow)

    negotiate_bytes = (
            b'v\x00\x00\x00\x1f'     # Tag 'v', Int32 Length: 31
            b'\x00\x00\x00\x00'     # Int32 Supported Minor Version: 0
            b'\x00\x00\x00\x02'             # Int32 Option Count: 2
            b'option_a\x00'         # Option string 1 + null byte
            b'option_b\x00'         # Option string 2 + null byte
        )
    test(negotiate_bytes, NegotiateProtocolVersion)

    auth_ok_bytes = (
        b'R'                  # Tag 'R'
        b'\x00\x00\x00\x08'  # Length: 8
        b'\x00\x00\x00\x00'  # Auth Code: 0 (Ok)
    )
    test(auth_ok_bytes, AuthenticationOk)

    error_response_bytes = (
        b'E'                  # Tag 'E' (or 'N' for Notice)
        b'\x00\x00\x00\x21'  # Length: 33
        b'S' b'ERROR\x00'     # Field 'S' (Severity): "ERROR"
        b'C' b'42601\x00'     # Field 'C' (Code): "42601" (syntax_error)
        b'M' b'syntax error\x00' # Field 'M' (Message): "syntax error"
        b'\x00'               # List-terminating null byte
    )
    test(error_response_bytes, ErrorResponse)

    backend_key_bytes = (
        b'K'                  # Tag 'K'
        b'\x00\x00\x00\x0c'  # Length: 12
        b'\x00\x00\x30\x39'  # Process ID: 12345
        b'\x00\x00\x16\x2e'  # Secret Key: 5678 (4 bytes / Int32)
    )
    test(backend_key_bytes, BackendKeyData)

    func_response_bytes = (
        b'V'                  # Tag 'V'
        b'\x00\x00\x00\x0c'  # Length: 12
        b'\x00\x00\x00\x04'  # Result Byte Length: 4
        b'data'               # 4 result bytes
    )
    test(func_response_bytes, FunctionCallResponse)

    func_response_null_bytes = (
        b'V'                  # Tag 'V'
        b'\x00\x00\x00\x08'  # Length: 8
        b'\xff\xff\xff\xff'  # Result Byte Length: -1 (NULL)
    )
    test(func_response_null_bytes, FunctionCallResponse)

    param_description_bytes = (
        b't'                  # Tag 't'
        b'\x00\x00\x00\x0e'  # Length: 14
        b'\x00\x02'          # Parameter Count: 2 (Int16)
        b'\x00\x00\x00\x17'  # OID 1: 23 (int4)
        b'\x00\x00\x00\x19'  # OID 2: 25 (text)
    )
    test(param_description_bytes, ParameterDescription)
