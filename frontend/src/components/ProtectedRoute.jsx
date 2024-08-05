import { Navigate } from "react-router-dom";
import api from "../api";
import { useAuth } from "../hooks/useAuth";


function ProtectedRoute({ children }) {
    
const { isAuthenticated } = useAuth();

if (isAuthenticated === null) {
    return <div>Loading...</div>;
}

return isAuthenticated ? children : <Navigate to="/login" />;
}
export default ProtectedRoute;