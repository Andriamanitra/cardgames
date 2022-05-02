function makeEl(elType) {
  return (props) => (strs, ...keys) => {
    let el = document.createElement(elType)
    props && Object.keys(props).forEach(prop => el[prop] = props[prop])
    el.innerText = strs.reduce((acc, x) => acc + keys.shift() + x)
    return el
  }
}

function elemGenFunc(elType) {
  return (...x) => {
    if (x[0] && typeof (x[0][0]) === "string") {
      return makeEl(elType)()(...x)
    } else {
      return makeEl(elType)(...x)
    }
  }
}
