export const devPrint = (...data) => {
    if (import.meta.env.VITE_ENV === 'development') {
        console.log(...data);
    }
}