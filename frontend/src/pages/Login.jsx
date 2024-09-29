import Form from "../components/Form";
import { useAuth } from "../hooks/useAuth";

function Login() {
  const { login } = useAuth();

  return (
    <>
      <button onClick={() => console.log(login("hoangng", "Hohohaha123@"))}>
        login
      </button>
      <Form route="/api/token/" method="login" />
    </>
  );
}

export default Login;
