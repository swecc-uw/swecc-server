export const devPrint = (...data) => {
  if (import.meta.env.DEV) {
    console.log(...data);
  } else {
    console.log(
      "This is a production build. Set import.meta.env.DEV to true to see console logs."
    );
  }
};
